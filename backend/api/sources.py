# pyrefly: ignore [missing-import]
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.session import get_db
from database.models import NewsSource
# pyrefly: ignore [missing-import]
from pydantic import BaseModel
from typing import List, Optional
import requests
import concurrent.futures
from collectors.hindi_news import HindiNewsCollector
from collectors.district_news import DistrictNewsCollector
from collectors.gov_news import GovernmentNewsCollector
from collectors.police_news import PoliceNewsCollector
from collectors.pib_news import PibNewsCollector
from api.auth import verify_api_key

router = APIRouter()


# Pydantic Schemas
class SourceCreate(BaseModel):
    name: str
    type: str
    url: str
    state: str
    district: Optional[str] = None
    department: Optional[str] = None
    category: Optional[str] = "General"


class SourceResponse(BaseModel):
    id: int
    name: str
    type: str
    url: str
    state: str
    district: Optional[str] = None
    department: Optional[str] = None
    category: Optional[str] = "General"
    is_active: bool

    class Config:
        from_attributes = True


class HealthCheckResponse(BaseModel):
    source_id: int
    name: str
    url: str
    status_code: Optional[int]
    is_reachable: bool


# Endpoints
@router.get("", response_model=List[SourceResponse])
def get_sources(db: Session = Depends(get_db), api_key: str = Depends(verify_api_key)):
    sources = db.query(NewsSource).all()
    return sources


@router.get("/filters")
def get_filters(db: Session = Depends(get_db), api_key: str = Depends(verify_api_key)):
    """
    Returns all unique states and their districts from active news sources.
    Used by the frontend to dynamically populate State/District dropdowns.
    """
    sources = db.query(NewsSource).filter(NewsSource.is_active == True).all()

    states_set = set()
    districts_by_state: dict = {}

    for source in sources:
        state = source.state
        district = source.district

        if not state or state in ("All", "National"):
            continue

        states_set.add(state)
        if state not in districts_by_state:
            districts_by_state[state] = set()
        if district and district not in ("All", ""):
            districts_by_state[state].add(district)

    result = {
        "states": ["All"] + sorted(states_set),
        "districts": {
            "All": ["All"],
            **{
                state: ["All"] + sorted(districts)
                for state, districts in sorted(districts_by_state.items())
            },
        },
    }
    return result


@router.post("", response_model=SourceResponse)
def add_source(source: SourceCreate, db: Session = Depends(get_db), api_key: str = Depends(verify_api_key)):
    db_source = db.query(NewsSource).filter(NewsSource.url == source.url).first()
    if db_source:
        raise HTTPException(status_code=400, detail="Source URL already exists")

    new_source = NewsSource(
        name=source.name,
        type=source.type,
        url=source.url,
        state=source.state,
        district=source.district,
        department=source.department,
        category=source.category,
        is_active=True,
    )
    db.add(new_source)
    db.commit()
    db.refresh(new_source)
    return new_source


@router.delete("/{source_id}")
def delete_source(source_id: int, db: Session = Depends(get_db), api_key: str = Depends(verify_api_key)):
    source = db.query(NewsSource).filter(NewsSource.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    db.delete(source)
    db.commit()
    return {"message": "Source deleted successfully"}


@router.put("/{source_id}/enable")
def enable_source(source_id: int, db: Session = Depends(get_db), api_key: str = Depends(verify_api_key)):
    source = db.query(NewsSource).filter(NewsSource.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    source.is_active = True
    db.commit()
    return {"message": "Source enabled"}


@router.put("/{source_id}/disable")
def disable_source(source_id: int, db: Session = Depends(get_db), api_key: str = Depends(verify_api_key)):
    source = db.query(NewsSource).filter(NewsSource.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    source.is_active = False
    db.commit()
    return {"message": "Source disabled"}


def check_url(source):
    try:
        # Use a short timeout so the health check endpoint returns quickly
        res = requests.head(
            source.url, timeout=3, headers={"User-Agent": "Mozilla/5.0"}
        )
        if res.status_code == 405:  # fallback to GET if HEAD is not allowed
            res = requests.get(
                source.url, timeout=3, headers={"User-Agent": "Mozilla/5.0"}
            )
        return {
            "source_id": source.id,
            "name": source.name,
            "url": source.url,
            "status_code": res.status_code,
            "is_reachable": res.status_code < 400,
        }
    except Exception:
        return {
            "source_id": source.id,
            "name": source.name,
            "url": source.url,
            "status_code": None,
            "is_reachable": False,
        }


@router.post("/health", response_model=List[HealthCheckResponse])
def check_sources_health(db: Session = Depends(get_db), api_key: str = Depends(verify_api_key)):
    active_sources = db.query(NewsSource).filter(NewsSource.is_active == True).all()
    results = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(check_url, src) for src in active_sources]
        for future in concurrent.futures.as_completed(futures):
            results.append(future.result())

    return results


@router.post("/{source_id}/retry")
def retry_source(source_id: int, db: Session = Depends(get_db), api_key: str = Depends(verify_api_key)):
    source = db.query(NewsSource).filter(NewsSource.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    # We will trigger the appropriate collector just for this source.
    # Note: In our current architecture, the collectors pull all active sources of their type.
    # For a pure retry of a single source, we can instantiate the collector and call parse_and_store directly if we fetch the feed.

    type_map = {
        "rss": HindiNewsCollector,
        "rss_district": DistrictNewsCollector,
        "rss_gov": GovernmentNewsCollector,
        "rss_police": PoliceNewsCollector,
        "rss_pib": PibNewsCollector,
    }

    collector_class = type_map.get(source.type)
    if not collector_class:
        raise HTTPException(
            status_code=400, detail=f"No collector implemented for type: {source.type}"
        )

    collector = collector_class(db)
    feed_xml = collector.fetch_feed_with_retry(source.url, max_retries=1)

    if not feed_xml:
        return {"status": "failed", "message": f"Failed to fetch {source.url}."}

    new_articles = collector.parse_and_store(feed_xml, source)

    return {
        "status": "success",
        "message": f"Retry complete. Fetched {new_articles} new articles from {source.name}.",
    }
