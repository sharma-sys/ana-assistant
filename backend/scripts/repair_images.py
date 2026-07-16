import os
import sys
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Ensure backend directory is in sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.models import NewsArticle
from services.image_extractor import ImageExtractor

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    logger.error("DATABASE_URL not set in .env")
    sys.exit(1)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def repair_article(article_id, url):
    extractor = ImageExtractor()
    try:
        image_url = extractor.extract_image(url)
        if image_url:
            return article_id, image_url, None
        return article_id, None, "No valid image found"
    except Exception as e:
        return article_id, None, str(e)

def main():
    db = SessionLocal()
    # Find all articles with no image, yield in chunks to prevent OOM
    articles = db.query(NewsArticle).filter(NewsArticle.image_url == None).yield_per(100)
    
    if not articles:
        logger.info("No articles found with missing images.")
        return
    logger.info("Found articles missing images. Starting repair...")
    
    success_count = 0
    fail_count = 0
    
    # Process in batches manually instead of loading everything into memory
    with ThreadPoolExecutor(max_workers=10) as executor:
        batch = []
        batch_size = 100
        
        def process_batch(current_batch):
            nonlocal success_count, fail_count
            future_to_article = {
                executor.submit(repair_article, a.id, a.source_url): a for a in current_batch
            }
            for future in as_completed(future_to_article):
                a = future_to_article[future]
                try:
                    article_id, img_url, error = future.result()
                    if img_url:
                        db_article = db.query(NewsArticle).filter(NewsArticle.id == article_id).first()
                        if db_article:
                            db_article.image_url = img_url
                            db.commit()
                            logger.info(f"Fixed image for article {article_id}: {img_url}")
                            success_count += 1
                    else:
                        logger.warning(f"Failed to find image for article {article_id} ({a.source_url}): {error}")
                        fail_count += 1
                except Exception as exc:
                    logger.error(f"Article {a.id} generated an exception: {exc}")
                    fail_count += 1

        for article in articles:
            batch.append(article)
            if len(batch) >= batch_size:
                process_batch(batch)
                batch = []
                
        if batch:
            process_batch(batch)
                
    logger.info(f"Repair complete. Success: {success_count}, Failed: {fail_count}")

if __name__ == "__main__":
    main()
