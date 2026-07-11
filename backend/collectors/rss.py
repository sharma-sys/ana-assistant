# pyrefly: ignore [missing-import]
import cloudscraper
# pyrefly: ignore [missing-import]
import feedparser
import logging
import time
import random
import re
import concurrent.futures
# pyrefly: ignore [missing-import]
from bs4 import BeautifulSoup
from datetime import datetime
from database.models import NewsArticle, NewsSource
from sqlalchemy.orm import Session
from utils.credibility import CredibilityEngine

logger = logging.getLogger(__name__)

class GenericRssCollector:
    def __init__(self, db: Session):
        self.db = db
        self.scraper = cloudscraper.create_scraper(
            browser={"browser": "chrome", "platform": "windows", "mobile": False}
        )

    def fetch_feed_with_retry(self, url: str, max_retries: int = 3) -> str | None:
        for attempt in range(max_retries):
            try:
                response = self.scraper.get(url, timeout=10)
                response.raise_for_status()
                return response.text
            except Exception as e:
                logger.error(
                    f"Attempt {attempt + 1}/{max_retries} failed for {url}: {e}"
                )
                time.sleep(2**attempt)
        logger.error(f"Failed to fetch {url} after {max_retries} attempts.")
        return None

    def extract_image(self, entry) -> str | None:
        image_url = None

        if hasattr(entry, "media_content") and len(entry.media_content) > 0:
            image_url = entry.media_content[0].get("url")
        elif hasattr(entry, "links"):
            for link in entry.links:
                if "image" in link.get("type", ""):
                    image_url = link.get("href")
                    break
        if not image_url and hasattr(entry, "description"):
            match = re.search(r'img.*?src="([^"]+)"', entry.description)
            if match:
                image_url = match.group(1)

        if not image_url and hasattr(entry, "link"):
            try:
                res = self.scraper.get(entry.link, timeout=3)
                if res.status_code == 200:
                    soup = BeautifulSoup(res.text, "html.parser")
                    og_image = soup.find("meta", property="og:image")
                    if og_image and og_image.get("content"):
                        image_url = og_image.get("content")
            except Exception:
                pass

        if not image_url:
            keywords = ["india", "government", "parliament", "flag", "ministry", "policy"]
            image_url = f"https://source.unsplash.com/800x600/?{random.choice(keywords)}"

        return image_url

    def _process_entry(self, entry, source):
        source_id = source.id
        source_state = source.state
        source_district = source.district
        department = source.department
        source_category = source.category
        published_dt = datetime.utcnow()
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            import time as parse_time
            published_dt = datetime.fromtimestamp(parse_time.mktime(entry.published_parsed))
        elif hasattr(entry, "published"):
            from dateutil import parser
            try:
                published_dt = parser.parse(entry.published).replace(tzinfo=None)
            except:
                pass

        # Try RSS feed metadata first, then scrape og:image from article page
        from utils.image_fetcher import extract_image_from_feed_entry, fetch_og_image
        image_url = extract_image_from_feed_entry(entry)
        if not image_url and hasattr(entry, "link"):
            image_url = fetch_og_image(entry.link, timeout=4)

        return NewsArticle(
            title=entry.get("title", "No Title"),
            source_url=entry.link,
            source_id=source_id,
            state=source_state,
            district=source_district,
            department=department,
            category=source_category,
            published_at=published_dt,
            status="pending",
            image_url=image_url,
        )
        
        # Calculate credibility upfront
        article.credibility_score = CredibilityEngine.calculate_score(article, source)
        return article

    def parse_and_store(self, feed_xml: str, source: NewsSource) -> int:
        from collectors.deduplicator import Deduplicator
        feed = feedparser.parse(feed_xml)
        new_count = 0
        if not feed.entries: return 0

        deduplicator = Deduplicator(self.db)
        unique_entries = []
        for entry in feed.entries:
            if not hasattr(entry, "link"): continue
            title = entry.get("title", "")
            link = entry.link
            if deduplicator.is_duplicate(title, link): continue
            unique_entries.append(entry)

        if not unique_entries: return 0

        articles_to_add = []
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(self._process_entry, entry, source) for entry in unique_entries]
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                if result: articles_to_add.append(result)

        if articles_to_add:
            for article in articles_to_add:
                self.db.add(article)
                new_count += 1
            try:
                self.db.commit()
            except Exception as e:
                self.db.rollback()
                logger.error(f"Failed to commit articles for {source.name}: {e}")
                return 0

        return new_count

    def run(self) -> dict:
        logger.info("Starting Generic RSS Collector run...")
        sources_to_process = self.db.query(NewsSource).filter(NewsSource.type == "rss", NewsSource.is_active == True).all()
        total_new_articles = 0
        skipped_sources = 0

        for source in sources_to_process:
            logger.info(f"Processing feed for {source.name}...")
            feed_xml = self.fetch_feed_with_retry(source.url)
            if feed_xml:
                new_articles = self.parse_and_store(feed_xml, source)
                total_new_articles += new_articles
                logger.info(f"Successfully processed {source.name}. New articles: {new_articles}")
            else:
                logger.warning(f"Skipping {source.name} due to fetch failure.")
                skipped_sources += 1

        return {"status": "success", "new_articles_count": total_new_articles, "skipped_sources": skipped_sources}
