"""
Bulk script to backfill missing image_url for existing articles.
Fetches og:image from article pages using ThreadPoolExecutor.
Run: python backfill_images.py [--limit N]
"""
import sys
import os
import logging
sys.path.insert(0, os.path.dirname(__file__))

import concurrent.futures
from database.session import SessionLocal
from database.models import NewsArticle
from utils.image_fetcher import fetch_og_image

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
logger = logging.getLogger(__name__)

BATCH_SIZE = 100
MAX_WORKERS = 20


def process_article(article_id: int, source_url: str):
    img = fetch_og_image(source_url, timeout=5)
    return article_id, img


def main():
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    db = SessionLocal()
    try:
        query = db.query(NewsArticle.id, NewsArticle.source_url).filter(
            (NewsArticle.image_url == None) | (NewsArticle.image_url == "")
        )
        if limit:
            query = query.limit(limit)
        articles = query.all()
        total = len(articles)
        logger.info(f"Found {total} articles without images. Starting backfill...")

        updated = 0
        failed = 0

        for i in range(0, total, BATCH_SIZE):
            batch = articles[i : i + BATCH_SIZE]
            with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
                futures = {
                    ex.submit(process_article, art.id, art.source_url): art.id
                    for art in batch
                }
                for future in concurrent.futures.as_completed(futures):
                    art_id, img_url = future.result()
                    if img_url:
                        db.query(NewsArticle).filter(NewsArticle.id == art_id).update(
                            {"image_url": img_url}
                        )
                        updated += 1
                    else:
                        failed += 1

            db.commit()
            logger.info(
                f"Progress: {min(i + BATCH_SIZE, total)}/{total} | "
                f"Updated: {updated} | Failed: {failed}"
            )

        logger.info(f"Done! Updated {updated}/{total} articles with images.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
