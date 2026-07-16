# pyrefly: ignore [missing-import]
from apscheduler.schedulers.background import BackgroundScheduler
from database.session import SessionLocal
from collectors.unified_news_collector import UnifiedNewsCollector
from database.models import NewsArticle, AIResult
from services.scraper_service import extract_article_content
from services.ai_service import ai_service
import logging
import json
import os

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()

def run_unified_collector():
    logger.info("Starting Unified News Collector...")
    db = SessionLocal()
    try:
        collector = UnifiedNewsCollector(db)
        result = collector.run()
        logger.info(result)
    except Exception as e:
        logger.error(f"Unified News Collector failed: {e}")
    finally:
        db.close()

def process_ai_queue():
    """Background worker to process queued AI generation requests"""
    db = SessionLocal()
    try:
        # Get one queued article to process
        article = db.query(NewsArticle).filter(NewsArticle.status == "queued").first()
        if not article:
            return

        logger.info(f"Processing AI generation for article {article.id}")
        
        # Check if result already exists to prevent duplicate generation
        existing = db.query(AIResult).filter(AIResult.article_id == article.id).first()
        if existing:
            article.status = "processed"
            db.commit()
            return

        # Extract content
        article_content = extract_article_content(article.source_url)
        
        # Call Gemini Provider synchronously (worker thread)
        ai_data = ai_service.generate_seo_content_sync(
            article_title=article.title, 
            article_content=article_content
        )

        if ai_data:
            # Combine tags and keywords for the keywords column
            raw_keywords = ai_data.get("keywords", [])
            raw_tags = ai_data.get("tags", [])
            
            if isinstance(raw_keywords, str):
                raw_keywords = [k.strip() for k in raw_keywords.split(",")]
            if isinstance(raw_tags, str):
                raw_tags = [t.strip() for t in raw_tags.split(",")]
                
            combined_keywords_list = list(set((raw_keywords if isinstance(raw_keywords, list) else []) + (raw_tags if isinstance(raw_tags, list) else [])))
            combined_keywords = ", ".join(combined_keywords_list)

            new_result = AIResult(
                article_id=article.id,
                content=ai_data.get("rewritten_article", ""),
                seo_title=ai_data.get("title", ""),
                meta_description=ai_data.get("meta_description", ""),
                keywords=combined_keywords,
                slug=ai_data.get("slug", ""),
                summary=(
                    "\n".join(f"- {point}" for point in ai_data.get("summary", []))
                    if isinstance(ai_data.get("summary"), list)
                    else ai_data.get("summary", "")
                ),
                category=ai_data.get("category", ""),
                reading_time=ai_data.get("reading_time", ""),
                translation=ai_data.get("translation", ""),
                related_articles=(
                    json.dumps(ai_data.get("related_articles", []))
                    if isinstance(ai_data.get("related_articles"), list)
                    else ai_data.get("related_articles", "")
                ),
            )
            article.status = "processed"
            db.add(new_result)
            db.commit()
            logger.info(f"Successfully generated AI content for article {article.id}")
        else:
            # Fallback or error, keep it queued or mark failed
            # We'll set it back to pending so it can be retried or ignored
            article.status = "pending" 
            db.commit()
            logger.error(f"Failed to generate AI data for article {article.id}")

    except Exception as e:
        logger.error(f"Error in AI Queue Processor: {e}", exc_info=True)
        db.rollback()
    finally:
        db.close()

COLLECTOR_INTERVAL = int(os.getenv("COLLECTOR_INTERVAL", "120"))

# Run the unified collector periodically based on env config
scheduler.add_job(
    run_unified_collector,
    "interval",
    seconds=COLLECTOR_INTERVAL,
    id="fetch_unified_news_job",
    replace_existing=True,
)

# Run the AI Queue processor very frequently (e.g., every 5 seconds)
# This acts as our background worker for Gemini generation
scheduler.add_job(
    process_ai_queue,
    "interval",
    seconds=5,
    id="process_ai_queue_job",
    replace_existing=True,
)
