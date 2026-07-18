# pyrefly: ignore [missing-import]
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from database.session import get_db
from database.models import NewsArticle, NewsSource
# pyrefly: ignore [missing-import]
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
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
        # Include articles tagged for the specific state OR for 'All' states (national/sports/international)
        query = query.filter(or_(NewsArticle.state == state, NewsArticle.state == "All"))
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
    """
    OPTIMIZED: Single query using Window Functions to get latest article per active source.
    Avoids fetching large subsets of rows and performs at millisecond speed.
    """
    from sqlalchemy import func

    # Subquery: Calculate row number per source ordered by published_at DESC
    rn = func.row_number().over(
        partition_by=NewsArticle.source_id,
        order_by=NewsArticle.published_at.desc()
    ).label('rn')
    
    subq = db.query(NewsArticle.id, rn)
    if state and state != "All":
        subq = subq.filter(or_(NewsArticle.state == state, NewsArticle.state == "All"))
    if district and district != "All":
        subq = subq.filter(NewsArticle.district == district)
    if category and category != "All":
        subq = subq.filter(NewsArticle.category == category)
    if search:
        subq = subq.filter(NewsArticle.title.ilike(f"%{search}%"))
    
    subq = subq.subquery()

    # Join to get the actual latest article per source (rn == 1)
    rows = (
        db.query(NewsArticle, NewsSource)
        .join(subq, NewsArticle.id == subq.c.id)
        .join(NewsSource, NewsArticle.source_id == NewsSource.id)
        .filter(NewsSource.is_active == True)
        .filter(subq.c.rn == 1)
        .order_by(NewsArticle.published_at.desc())
        .limit(16)
        .all()
    )

    items = []
    for article, source in rows:
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
    """
    OPTIMIZED: Safely fetches exactly the top 10 articles per source using ROW_NUMBER.
    Avoids fetching excessive subsets, memory bloat, and solves the single-source bug.
    """
    from sqlalchemy import func

    # Subquery: Calculate row number per source ordered by published_at DESC
    rn = func.row_number().over(
        partition_by=NewsArticle.source_id,
        order_by=NewsArticle.published_at.desc()
    ).label('rn')
    
    subq = db.query(NewsArticle.id, rn)
    if state and state != "All":
        subq = subq.filter(or_(NewsArticle.state == state, NewsArticle.state == "All"))
    if district and district != "All":
        subq = subq.filter(NewsArticle.district == district)
    if category and category != "All":
        subq = subq.filter(NewsArticle.category == category)
    if search:
        subq = subq.filter(NewsArticle.title.ilike(f"%{search}%"))
    
    subq = subq.subquery()

    # Fetch exactly the top 10 rows per active source
    all_rows = (
        db.query(NewsArticle, NewsSource)
        .join(subq, NewsArticle.id == subq.c.id)
        .join(NewsSource, NewsArticle.source_id == NewsSource.id)
        .filter(NewsSource.is_active == True)
        .filter(subq.c.rn <= 10)
        .order_by(NewsArticle.source_id, subq.c.rn)
        .all()
    )

    grouped: dict = {}
    for article, source in all_rows:
        sname = source.name
        if sname not in grouped:
            grouped[sname] = []
            
        grouped[sname].append(
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
                source_name=sname,
                references=article.references,
            )
        )

    return grouped




def run_rss_collectors():
    from database.session import SessionLocal
    db = SessionLocal()
    try:
        from collectors.unified_news_collector import UnifiedNewsCollector
        logger = logging.getLogger(__name__)
        logger.info("Triggering UnifiedNewsCollector manually.")
        collector = UnifiedNewsCollector(db)
        result = collector.run()
        logger.info(result)
    except Exception as e:
        import logging
        logging.error(f"Error fetching feeds: {str(e)}", exc_info=True)
    finally:
        db.close()


@router.post("/fetch")
def trigger_rss_fetch(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db), 
    api_key: str = Depends(verify_api_key)
):
    try:
        background_tasks.add_task(run_rss_collectors)
        return {"status": "success", "new_articles_count": "all"}
    except Exception as e:
        import logging
        logging.error(f"Error fetching RSS feeds: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
