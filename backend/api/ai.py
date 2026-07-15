# pyrefly: ignore [missing-import]
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.session import get_db
from database.models import NewsArticle, AIResult
# pyrefly: ignore [missing-import]
from pydantic import BaseModel
import logging
from api.auth import verify_api_key

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

@router.post("/generate")
def request_ai_generation(
    req: GenerateRequest, 
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """
    Non-blocking endpoint that queues an article for AI generation.
    Frontend should poll /result/{article_id} for the final output.
    """
    article = db.query(NewsArticle).filter(NewsArticle.id == req.article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    existing = db.query(AIResult).filter(AIResult.article_id == article.id).first()
    if existing:
        return {"status": "completed", "article_id": article.id}

    if article.status != "queued":
        article.status = "queued"
        db.commit()

    return {"status": "queued", "article_id": article.id}

@router.get("/result/{article_id}")
def get_ai_result(
    article_id: int,
    db: Session = Depends(get_db)
):
    """
    Polling endpoint for frontend to get generated AI result.
    """
    article = db.query(NewsArticle).filter(NewsArticle.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    existing = db.query(AIResult).filter(AIResult.article_id == article.id).first()
    if existing:
        return {
            "status": "completed",
            "data": {
                "content": existing.content,
                "seo_title": existing.seo_title,
                "meta_description": existing.meta_description,
                "keywords": existing.keywords,
                "slug": existing.slug,
                "summary": existing.summary,
                "category": existing.category,
                "reading_time": existing.reading_time,
                "translation": existing.translation,
                "related_articles": existing.related_articles
            }
        }
    
    if article.status == "queued":
        return {"status": "processing"}
        
    return {"status": "pending"}
