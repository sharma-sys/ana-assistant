# pyrefly: ignore [missing-import]
from fastapi import FastAPI
# pyrefly: ignore [missing-import]
from fastapi.middleware.cors import CORSMiddleware
from database.session import engine, Base
from api import news, ai, sources
from contextlib import asynccontextmanager
from scheduler.jobs import scheduler
import logging
import sys
# pyrefly: ignore [missing-import]
from fastapi.responses import JSONResponse
# pyrefly: ignore [missing-import]
from fastapi import Request

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("ana_backend")

# Create database tables
Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup event
    logger.info("Starting up ANA Backend (Scheduler now runs in worker.py)")
    yield
    # Shutdown event
    logger.info("Shutting down ANA Backend")


import os

app = FastAPI(title="ANA Backend", version="1.0.0", lifespan=lifespan)

allowed_origins_str = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")
allowed_origins = [origin.strip() for origin in allowed_origins_str.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception occurred: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"message": "An internal server error occurred."},
    )

app.include_router(news.router, prefix="/api/news", tags=["News"])
app.include_router(ai.router, prefix="/api/ai", tags=["AI"])
app.include_router(sources.router, prefix="/api/sources", tags=["Sources"])


@app.get("/api/health")
def read_root():
    return {"message": "Welcome to the AAYUDH News Assistant API"}
