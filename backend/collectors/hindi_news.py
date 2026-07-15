from sqlalchemy.orm import clsregistry
from sqlalchemy.orm import clsregistry
import time
import logging
import re
import requests
# pyrefly: ignore [missing-import]
import feedparser
from datetime import datetime
# pyrefly: ignore [missing-import]
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session
from database.models import NewsSource, NewsArticle
import random

logger = logging.getLogger(__name__)

# Removed Spacy NLP to avoid heavy computational overhead.
# City extraction now uses a fast deterministic list approach.


class HindiNewsCollector:
    """
    Modular collector specifically designed for Hindi News sources.
    Features:
    - Official RSS support
    - Configurable timeout and retries
    - Metadata-only extraction
    - Duplicate prevention
    - Comprehensive logging
    """

    def __init__(self, db: Session, max_retries: int = 3, timeout_sec: int = 10):
        self.db = db
        self.max_retries = max_retries
        self.timeout_sec = timeout_sec

    def fetch_feed_with_retry(self, url: str, max_retries: int | None = None) -> str | None:
        """
        Fetches the RSS feed XML using cloudscraper with timeouts and retries.
        """
        attempt = 0
        effective_retries = max_retries if max_retries is not None else self.max_retries
        while attempt < effective_retries:
            try:
                # Add headers to act like a normal browser and avoid blocking
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                }
                # Fallback to cloudscraper for bypass
                try:
                    # pyrefly: ignore [missing-import]
                    import cloudscraper

                    scraper = cloudscraper.create_scraper()
                    response = scraper.get(
                        url, headers=headers, timeout=self.timeout_sec
                    )
                except ImportError:
                    response = requests.get(
                        url, headers=headers, timeout=self.timeout_sec
                    )

                response.raise_for_status()
                return response.text
            except requests.exceptions.RequestException as e:
                attempt += 1
                logger.warning(
                    f"Attempt {attempt}/{self.max_retries} failed for {url}: {e}"
                )
                if attempt < self.max_retries:
                    time.sleep(2**attempt)  # Exponential backoff: 2s, 4s, 8s

        logger.error(f"Failed to fetch {url} after {self.max_retries} attempts.")
        return None

    def extract_city(self, text: str) -> str:
        """Extract city from title/description using fast substring matching"""
        district = "Unknown"
        try:
            text_lower = text.lower()

            # Expanded list of major Indian cities (English and Hindi/Devanagari)
            city_map = {
                "bhopal": "Bhopal",
                "भोपाल": "Bhopal",
                "indore": "Indore",
                "इंदौर": "Indore",
                "lucknow": "Lucknow",
                "लखनऊ": "Lucknow",
                "patna": "Patna",
                "पटना": "Patna",
                "mumbai": "Mumbai",
                "मुंबई": "Mumbai",
                "pune": "Pune",
                "पुणे": "Pune",
                "delhi": "Delhi",
                "दिल्ली": "Delhi",
                "नई दिल्ली": "Delhi",
                "new delhi": "Delhi",
                "bangalore": "Bengaluru",
                "bengaluru": "Bengaluru",
                "बेंगलुरु": "Bengaluru",
                "chennai": "Chennai",
                "चेन्नई": "Chennai",
                "kolkata": "Kolkata",
                "कोलकाता": "Kolkata",
                "hyderabad": "Hyderabad",
                "हैदराबाद": "Hyderabad",
                "ahmedabad": "Ahmedabad",
                "अहमदाबाद": "Ahmedabad",
                "jaipur": "Jaipur",
                "जयपुर": "Jaipur",
                "kanpur": "Kanpur",
                "कानपुर": "Kanpur",
                "nagpur": "Nagpur",
                "नागपुर": "Nagpur",
                "surat": "Surat",
                "सूरत": "Surat",
                "ranchi": "Ranchi",
                "रांची": "Ranchi",
                "raipur": "Raipur",
                "रायपुर": "Raipur",
                "dehradun": "Dehradun",
                "देहरादून": "Dehradun",
                "shimla": "Shimla",
                "शिमला": "Shimla",
                "chandigarh": "Chandigarh",
                "चंडीगढ़": "Chandigarh",
                "varanasi": "Varanasi",
                "वाराणसी": "Varanasi",
                "kashi": "Varanasi",
                "काशी": "Varanasi",
                "agra": "Agra",
                "आगरा": "Agra",
            }

            for key, standardized_name in city_map.items():
                if key in text_lower:
                    return standardized_name

        except Exception as e:
            logger.warning(f"City extraction failed: {e}")

        return district

    def extract_image(self, entry) -> str | None:
        """Extract best image from the RSS entry, then scrape og:image if needed."""
        from utils.image_fetcher import extract_image_from_feed_entry, fetch_og_image
        # Try RSS metadata first (fast, no HTTP request)
        image_url = extract_image_from_feed_entry(entry)
        # Fallback: scrape og:image from article page
        if not image_url and hasattr(entry, "link"):
            image_url = fetch_og_image(entry.link, timeout=4)
        return image_url

    def _process_entry(self, entry, source_id, source_state, source_category):
        # Parse Date
        published_dt = datetime.utcnow()
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            import time as parse_time

            published_dt = datetime.fromtimestamp(
                parse_time.mktime(entry.published_parsed)
            )
        elif hasattr(entry, "published"):
            from dateutil import parser

            try:
                published_dt = parser.parse(entry.published).replace(tzinfo=None)
            except:
                pass

        # Extract Metadata (image scraping can be slow, so concurrent thread is good here)
        text_for_city = f"{entry.get('title', '')} {entry.get('description', '')}"
        city = self.extract_city(text_for_city)
        image_url = self.extract_image(entry)

        return NewsArticle(
            title=entry.get("title", "No Title"),
            source_url=entry.link,
            source_id=source_id,
            state=source_state,
            district=city,
            category=source_category,
            published_at=published_dt,
            status="pending",
            image_url=image_url,
        )

    def parse_and_store(self, feed_xml: str, source: NewsSource) -> int:
        """
        Parses XML string using feedparser and stores *metadata only* in DB.
        Prevents duplicate URLs. Uses ThreadPoolExecutor for faster processing.
        """
        from collectors.deduplicator import Deduplicator

        feed = feedparser.parse(feed_xml)
        new_count = 0

        if not feed.entries:
            return 0

        deduplicator = Deduplicator(self.db)

        unique_entries = []
        for entry in feed.entries:
            if not hasattr(entry, "link"):
                continue
            title = entry.get("title", "")
            link = entry.link

            if deduplicator.is_duplicate(title, link):
                continue

            unique_entries.append(entry)

        if not unique_entries:
            return 0

        import concurrent.futures

        articles_to_add = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [
                executor.submit(
                    self._process_entry, entry, source.id, source.state, source.category
                )
                for entry in unique_entries
            ]
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                if result:
                    articles_to_add.append(result)

        if articles_to_add:
            for article in articles_to_add:
                try:
                    self.db.add(article)
                    self.db.commit()
                    new_count += 1
                except Exception as e:
                    self.db.rollback()

        return new_count

    def run(self) -> dict:
        """
        Main execution flow.
        """
        logger.info("Starting Hindi News Collector...")
        # We fetch sources where type == 'rss' and language isn't explicitly defined, but we can check if it's our list.
        # Wait, the current model `NewsSource` does not have a `language` or `type=rss_hindi`.
        # Earlier we inserted Hindi feeds with type='rss'.
        # Let's filter by the known Hindi feeds or just rely on a new field.
        # For simplicity, we can fetch all where url matches Hindi feeds or just create them with a specific state/tag.

        # Let's just create/fetch them natively inside this method for phase 1
        official_hindi_sources = [
            {
                "name": "Aaj Tak - Hindi",
                "url": "https://www.aajtak.in/rssfeeds/?id=home",
            },
            {"name": "ABP News - Hindi", "url": "https://www.abplive.com/home/feed"},
            {
                "name": "Zee News - Hindi",
                "url": "https://zeenews.india.com/hindi/india/rss",
            },
            {
                "name": "News18 - Hindi",
                "url": "https://hindi.news18.com/rss/khabar/nation/nation.xml",
            },
            {
                "name": "India TV - Hindi",
                "url": "https://www.indiatv.in/rssnews/topstory.xml",
            },
            {
                "name": "NDTV Khabar - Hindi",
                "url": "https://feeds.feedburner.com/ndtvkhabar-latest",
            },
            {"name": "TV9 Bharatvarsh - Hindi", "url": "https://tv9hindi.com/feed"},
            {"name": "BBC Hindi", "url": "https://feeds.bbci.co.uk/hindi/rss.xml"},
            {"name": "DW Hindi", "url": "https://rss.dw.com/xml/rss-hin-all"},
            {
                "name": "OneIndia Hindi",
                "url": "https://hindi.oneindia.com/rss/hindi-india-fb.xml",
            },
        ]

        # Ensure they exist in DB, and use them
        sources_to_process = []
        for s in official_hindi_sources:
            db_source = (
                self.db.query(NewsSource).filter(NewsSource.url == s["url"]).first()
            )
            if not db_source:
                db_source = NewsSource(
                    name=s["name"],
                    type="rss_hindi",
                    url=s["url"],
                    state="All",
                    is_active=True,
                )
                self.db.add(db_source)
                self.db.commit()
            sources_to_process.append(db_source)

        # We also query any other 'rss_hindi' from DB just in case
        additional_sources = (
            self.db.query(NewsSource)
            .filter(NewsSource.is_active == True, NewsSource.type == "rss_hindi")
            .all()
        )
        for a_s in additional_sources:
            if a_s not in sources_to_process:
                sources_to_process.append(a_s)

        total_new_articles = 0
        for source in sources_to_process:
            logger.info(f"Processing feed for {source.name}...")
            feed_xml = self.fetch_feed_with_retry(source.url)
            if feed_xml:
                new_articles = self.parse_and_store(feed_xml, source)
                total_new_articles += new_articles
                logger.info(
                    f"Successfully processed {source.name}. New articles: {new_articles}"
                )
            else:
                logger.error(f"Skipping {source.name} due to fetch failure.")

        logger.info(
            f"Hindi News Collection complete. Total new articles: {total_new_articles}"
        )
        return {"status": "success", "new_articles_count": total_new_articles}
