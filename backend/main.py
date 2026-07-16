# pyrefly: ignore [missing-import]
from fastapi import FastAPI
# pyrefly: ignore [missing-import]
from fastapi.middleware.cors import CORSMiddleware
from database.session import engine, Base, SessionLocal
from database.models import NewsSource
from api import news, ai, sources
from contextlib import asynccontextmanager
from scheduler.jobs import scheduler
import logging
import sys
import os
# pyrefly: ignore [missing-import]
from fastapi.responses import JSONResponse
# pyrefly: ignore [missing-import]
from fastapi import Request
# pyrefly: ignore [missing-import]
from fastapi.middleware.gzip import GZipMiddleware

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("ana_backend")

# Create database tables (Removed for production, use alembic)
Base.metadata.create_all(bind=engine)

def seed_db():
    db = SessionLocal()
    try:
        count = db.query(NewsSource).count()
        if count == 0:
            logger.info("Seeding database with default news sources...")
            new_sources = [
                ("NDTV Hindi", "rss_hindi", "https://feeds.feedburner.com/ndtvkhabar-latest", "All", 1, None, None, "National"),
                ("News18 Hindi", "rss_hindi", "https://hindi.news18.com/rss/khabar/nation/nation.xml", "All", 1, None, None, "National"),
                ("BBC Hindi", "rss_hindi", "https://feeds.bbci.co.uk/hindi/rss.xml", "All", 1, None, None, "National"),
                ("Amar Ujala", "rss_hindi", "https://www.amarujala.com/rss/india-news.xml", "All", 1, None, None, "National"),
                ("Hindustan Times", "rss", "https://www.hindustantimes.com/feeds/rss/india-news/rssfeed.xml", "All", 1, None, None, "National"),
                ("Indian Express", "rss", "https://indianexpress.com/section/india/feed/", "All", 1, None, None, "National"),
                ("Times of India", "rss", "https://timesofindia.indiatimes.com/rssfeedstopstories.cms", "All", 1, None, None, "National"),
                ("The Hindu", "rss", "https://www.thehindu.com/news/national/feeder/default.rss", "All", 1, None, None, "National"),
                ("Lalluram", "rss_hindi", "https://lalluram.com/feed/", "Madhya Pradesh", 1, None, None, "Regional"),
                ("News18 MP", "rss_hindi", "https://hindi.news18.com/rss/khabar/madhya-pradesh/madhya-pradesh.xml", "Madhya Pradesh", 1, None, None, "Regional"),
                ("Webdunia MP", "rss_hindi", "https://hindi.webdunia.com/rss/regional-madhya-pradesh.xml", "Madhya Pradesh", 1, None, None, "Regional"),
                ("IBC24 MP", "rss_hindi", "https://www.ibc24.in/category/madhya-pradesh/feed", "Madhya Pradesh", 1, None, None, "Regional"),
                ("MP Breaking News", "rss_hindi", "https://mpbreakingnews.in/feed/", "Madhya Pradesh", 1, None, None, "Regional"),
                ("Khabar Satta", "rss_hindi", "https://khabarsatta.com/feed/", "Madhya Pradesh", 1, None, None, "Regional"),
                ("Bhopal Samachar", "rss_hindi", "https://www.bhopalsamachar.com/feeds/posts/default?alt=rss", "Madhya Pradesh", 1, None, None, "Regional"),
                ("Agniban", "rss_hindi", "https://www.agniban.com/feed/", "Madhya Pradesh", 1, None, None, "Regional"),
                # Sports
                ("ESPN Cricinfo", "rss", "https://www.espncricinfo.com/rss/content/story/feeds/0.xml", "All", 1, None, None, "Sports"),
                ("BBC Sport", "rss", "https://feeds.bbci.co.uk/sport/rss.xml", "All", 1, None, None, "Sports"),
                ("Amar Ujala Sports", "rss_hindi", "https://www.amarujala.com/rss/sports.xml", "All", 1, None, None, "Sports"),
                ("News18 Sports", "rss_hindi", "https://hindi.news18.com/rss/khabar/sports/sports.xml", "All", 1, None, None, "Sports"),
                # International
                ("BBC World News", "rss", "https://feeds.bbci.co.uk/news/world/rss.xml", "All", 1, None, None, "International"),
                ("BBC Hindi International", "rss_hindi", "https://feeds.bbci.co.uk/hindi/international/rss.xml", "All", 1, None, None, "International"),
                ("Al Jazeera English", "rss", "https://www.aljazeera.com/xml/rss/all.xml", "All", 1, None, None, "International"),
            ]
            for src in new_sources:
                ns = NewsSource(name=src[0], type=src[1], url=src[2], state=src[3], is_active=True, district=src[5], department=src[6], category=src[7])
                db.add(ns)
            db.commit()
    except Exception as e:
        logger.error(f"Failed to seed db: {e}")
    finally:
        db.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup event
    logger.info("Starting up ANA Backend (Scheduler now runs in worker.py)")
    seed_db()
    yield
    # Shutdown event
    logger.info("Shutting down ANA Backend")


app = FastAPI(title="ANA Backend", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception occurred: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"message": "An internal server error occurred."},
    )

app.include_router(news.router, prefix="/api/news", tags=["News"])
app.include_router(ai.router, prefix="/api/rewrite", tags=["AI"])
app.include_router(sources.router, prefix="/api/sources", tags=["Sources"])


@app.get("/api/health")
def read_root():
    return {"message": "Welcome to the AAYUDH News Assistant API"}
