# pyrefly: ignore [missing-import]
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.session import get_db
from database.models import NewsArticle, AIResult
# pyrefly: ignore [missing-import]
from pydantic import BaseModel
from services import ai_service, scraper_service
import json
import logging
from api.auth import verify_api_key
# pyrefly: ignore [missing-import]
from fastapi.concurrency import run_in_threadpool

logger = logging.getLogger(__name__)

router = APIRouter()


class GenerateRequest(BaseModel):
    article_id: int


class AIResultResponse(BaseModel):
    content: str
    seo_title: str
    meta_description: str
    keywords: str
    slug: str
    summary: str | None = None
    category: str | None = None
    reading_time: str | None = None
    translation: str | None = None
    related_articles: str | None = None

    class Config:
        from_attributes = True


@router.post("/generate", response_model=AIResultResponse)
def generate_ai_content(
    req: GenerateRequest, 
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    try:
        article = db.query(NewsArticle).filter(NewsArticle.id == req.article_id).first()
        if not article:
            raise HTTPException(status_code=404, detail="Article not found")

        existing = db.query(AIResult).filter(AIResult.article_id == article.id).first()
        if existing:
            return existing

        article_content = scraper_service.extract_article_content(article.source_url)
        
        ai_data = ai_service.generate_seo_content_sync(
            article_title=article.title, article_content=article_content
        )

        if not ai_data:
            raise HTTPException(status_code=500, detail="Failed to generate AI content")

        new_result = AIResult(
            article_id=article.id,
            content=ai_data.get("content", ""),
            seo_title=ai_data.get("seo_title", ""),
            meta_description=ai_data.get("meta_description", ""),
            keywords=(
                ", ".join(ai_data.get("keywords", []))
                if isinstance(ai_data.get("keywords"), list)
                else ai_data.get("keywords", "")
            ),
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
        db.refresh(new_result)

        return new_result
    except Exception as e:
        logger.error(f"Error in generate_ai_content: {e}", exc_info=True)
            
        err_msg = str(e).lower()
        if "429" in err_msg or "quota" in err_msg:
            raise HTTPException(status_code=429, detail="AI Service is currently busy (Rate Limit). Please wait a few seconds and try again.")
        raise HTTPException(status_code=500, detail=f"Failed to generate AI content: {str(e)}")
