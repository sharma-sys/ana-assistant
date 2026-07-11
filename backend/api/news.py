# pyrefly: ignore [missing-import]
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from database.session import get_db
from database.models import NewsArticle, NewsSource
# pyrefly: ignore [missing-import]
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from collectors.rss import GenericRssCollector
from utils.credibility import CredibilityEngine
from api.auth import verify_api_key

router = APIRouter()


class NewsArticleResponse(BaseModel):
    id: int
    title: str
    source_url: str
    state: Optional[str] = None
    district: Optional[str] = None
    department: Optional[str] = None
    category: Optional[str] = None
    published_at: datetime
    status: str
    image_url: Optional[str] = None
    language: Optional[str] = "hi"
    source_name: Optional[str] = None
    references: Optional[str] = None
    credibility_score: Optional[int] = None
    credibility_status: Optional[str] = None

    class Config:
        from_attributes = True


class PaginatedNewsResponse(BaseModel):
    items: List[NewsArticleResponse]
    total: int
    page: int
    pages: int


@router.get("/", response_model=PaginatedNewsResponse)
def get_news(
    state: Optional[str] = None,
    district: Optional[str] = None,
    category: Optional[str] = None,
    source: Optional[str] = None,
    search: Optional[str] = None,
    page: int = 1,
    limit: int = 50,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    query = db.query(NewsArticle, NewsSource).join(
        NewsSource, NewsArticle.source_id == NewsSource.id
    )

    if state and state != "All":
        query = query.filter(NewsArticle.state == state)
    if district and district != "All":
        query = query.filter(NewsArticle.district == district)
    if category and category != "All":
        query = query.filter(NewsArticle.category == category)
    if source and source != "All":
        query = query.filter(NewsSource.name.ilike(f"%{source}%"))
    if search:
        query = query.filter(NewsArticle.title.ilike(f"%{search}%"))

    total = query.count()
    pages = (total + limit - 1) // limit if limit > 0 else 1
    db_items = (
        query.order_by(NewsArticle.published_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )

    # Map the tuple (NewsArticle, NewsSource) to our response schema
    items = []
    for article, source in db_items:
        score = article.credibility_score or 50
        status = "Needs Verification"
        if score >= 90:
            status = "Highly Credible"
        elif score >= 75:
            status = "Credible"
        elif score >= 50:
            status = "Moderate"
            
        items.append(
            NewsArticleResponse(
                id=article.id,
                title=article.title,
                source_url=article.source_url,
                state=article.state,
                district=article.district,
                department=article.department,
                category=article.category,
                published_at=article.published_at,
                status=article.status,
                image_url=article.image_url,
                language=article.language,
                source_name=source.name,
                references=article.references,
                credibility_score=score,
                credibility_status=status,
            )
        )

    return {"items": items, "total": total, "page": page, "pages": pages}


@router.get("/top-grid", response_model=List[NewsArticleResponse])
def get_top_grid_news(
    state: Optional[str] = None,
    district: Optional[str] = None,
    category: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    active_sources = db.query(NewsSource).filter(NewsSource.is_active == True).all()
    items = []
    
    for source in active_sources:
        query = db.query(NewsArticle).filter(NewsArticle.source_id == source.id)
        
        if state and state != "All":
            query = query.filter(NewsArticle.state == state)
        if district and district != "All":
            query = query.filter(NewsArticle.district == district)
        if category and category != "All":
            query = query.filter(NewsArticle.category == category)
        if search:
            query = query.filter(NewsArticle.title.ilike(f"%{search}%"))
            
        article = query.order_by(NewsArticle.published_at.desc()).first()
        
        if article:
            report = CredibilityEngine.generate_fact_check_report(article, source)
            items.append(
                NewsArticleResponse(
                    id=article.id,
                    title=article.title,
                    source_url=article.source_url,
                    state=article.state,
                    district=article.district,
                    department=article.department,
                    category=article.category,
                    published_at=article.published_at,
                    status=article.status,
                    image_url=article.image_url,
                    language=article.language,
                    source_name=source.name,
                    references=article.references,
                    credibility_score=report["credibility_score"],
                    credibility_status=report["status"],
                )
            )
            
    # Sort by most recently published overall
    items.sort(key=lambda x: x.published_at, reverse=True)
    
    # Ensure exactly 16 items for a 4x4 grid
    if len(items) > 16:
        items = items[:16]
    elif len(items) < 16:
        existing_ids = [item.id for item in items]
        additional_needed = 16 - len(items)
        
        query = (
            db.query(NewsArticle, NewsSource)
            .join(NewsSource, NewsArticle.source_id == NewsSource.id)
            .filter(~NewsArticle.id.in_(existing_ids))
        )
        
        if state and state != "All":
            query = query.filter(NewsArticle.state == state)
        if district and district != "All":
            query = query.filter(NewsArticle.district == district)
        if category and category != "All":
            query = query.filter(NewsArticle.category == category)
        if search:
            query = query.filter(NewsArticle.title.ilike(f"%{search}%"))
            
        more_articles = query.order_by(NewsArticle.published_at.desc()).limit(additional_needed).all()
        
        for article, source in more_articles:
            report = CredibilityEngine.generate_fact_check_report(article, source)
            items.append(
                NewsArticleResponse(
                    id=article.id,
                    title=article.title,
                    source_url=article.source_url,
                    state=article.state,
                    district=article.district,
                    department=article.department,
                    category=article.category,
                    published_at=article.published_at,
                    status=article.status,
                    image_url=article.image_url,
                    language=article.language,
                    source_name=source.name,
                    references=article.references,
                    credibility_score=report["credibility_score"],
                    credibility_status=report["status"],
                )
            )
            
    return items


@router.get("/pramukh-samachar", response_model=dict)
def get_pramukh_samachar(
    state: Optional[str] = None,
    district: Optional[str] = None,
    category: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    active_sources = db.query(NewsSource).filter(NewsSource.is_active == True).all()
    grouped = {}
    
    for source in active_sources:
        query = db.query(NewsArticle).filter(NewsArticle.source_id == source.id)
        
        if state and state != "All":
            query = query.filter(NewsArticle.state == state)
        if district and district != "All":
            query = query.filter(NewsArticle.district == district)
        if category and category != "All":
            query = query.filter(NewsArticle.category == category)
        if search:
            query = query.filter(NewsArticle.title.ilike(f"%{search}%"))
            
        articles = query.order_by(NewsArticle.published_at.desc()).limit(10).all()
        
        if articles:
            grouped[source.name] = []
            for article in articles:
                grouped[source.name].append(
                    NewsArticleResponse(
                        id=article.id,
                        title=article.title,
                        source_url=article.source_url,
                        state=article.state,
                        district=article.district,
                        department=article.department,
                        category=article.category,
                        published_at=article.published_at,
                        status=article.status,
                        image_url=article.image_url,
                        language=article.language,
                        source_name=source.name,
                        references=article.references,
                    )
                )
                
    return grouped



def run_rss_collectors(db: Session):
    try:
        from collectors.rss import GenericRssCollector
        from collectors.hindi_news import HindiNewsCollector
        from collectors.gov_news import GovernmentNewsCollector
        from collectors.district_news import DistrictNewsCollector
        
        c1 = GenericRssCollector(db)
        c1.run()
        
        c2 = HindiNewsCollector(db)
        c2.run()
        
        c3 = GovernmentNewsCollector(db)
        c3.run()

        c4 = DistrictNewsCollector(db)
        c4.run()
    except Exception as e:
        import logging
        logging.error(f"Error fetching RSS feeds: {str(e)}", exc_info=True)


@router.post("/fetch")
def trigger_rss_fetch(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db), 
    api_key: str = Depends(verify_api_key)
):
    try:
        background_tasks.add_task(run_rss_collectors, db)
        return {"status": "success", "new_articles_count": "all"}
    except Exception as e:
        import logging
        logging.error(f"Error fetching RSS feeds: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
