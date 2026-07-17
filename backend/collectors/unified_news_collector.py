import os
import time
import json
import logging
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import List, Dict, Any
from urllib.parse import urlparse

import feedparser
import requests
from bs4 import BeautifulSoup
import cloudscraper
import lxml

from sqlalchemy.orm import Session
from database.models import NewsSource, NewsArticle
from collectors.deduplicator import Deduplicator
from services.scraper_service import _enforce_rate_limit

logger = logging.getLogger(__name__)

# Config
MAX_WORKERS = int(os.getenv("MAX_WORKERS", "10"))
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "15"))
RETRY_LIMIT = int(os.getenv("RETRY_LIMIT", "3"))

class UnifiedNewsCollector:
    def __init__(self, db: Session):
        self.db = db
        self.deduplicator = Deduplicator(db)
        self.scraper = cloudscraper.create_scraper()
        from services.image_extractor import ImageExtractor
        self.image_extractor = ImageExtractor()

    def _get_og_image(self, url: str) -> str:
        try:
            resp = self.scraper.get(url, timeout=REQUEST_TIMEOUT)
            if resp.status_code == 200:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(resp.content, 'html.parser')
                og_img = soup.find('meta', property='og:image')
                if og_img and og_img.get('content'):
                    return og_img['content']
        except Exception as e:
            logger.warning(f"Failed to fetch og:image for {url}: {e}")
        return None

    def fetch_with_backoff(self, url: str) -> requests.Response:
        """Fetch URL with exponential backoff and timeout protection."""
        _enforce_rate_limit(url)
        
        for attempt in range(RETRY_LIMIT):
            try:
                response = self.scraper.get(url, timeout=REQUEST_TIMEOUT)
                response.raise_for_status()
                return response
            except requests.RequestException as e:
                logger.warning(f"Attempt {attempt + 1} failed for {url}: {e}")
                if attempt == RETRY_LIMIT - 1:
                    raise e
                time.sleep(2 ** attempt + random.uniform(0.1, 1.0))
        return None

    def process_rss(self, source: NewsSource) -> List[Dict[str, Any]]:
        articles = []
        try:
            # We can use feedparser directly since it handles XML/RSS very well
            response = self.fetch_with_backoff(source.url)
            feed = feedparser.parse(response.content)
            
            for entry in feed.entries:
                link = entry.get('link', '')
                title = entry.get('title', '')
                if not link or not title:
                    continue
                
                # Image extraction
                image_url = None
                if 'media_content' in entry and len(entry.media_content) > 0:
                    image_url = entry.media_content[0].get('url')
                elif 'media_thumbnail' in entry and len(entry.media_thumbnail) > 0:
                    image_url = entry.media_thumbnail[0].get('url')
                elif 'links' in entry:
                    for l in entry.links:
                        if 'image' in l.get('type', ''):
                            image_url = l.get('href')
                
                # Fallback to checking the description for an <img> tag if no RSS media image
                if not image_url and entry.get('description'):
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(entry.description, 'html.parser')
                    img_tag = soup.find('img')
                    if img_tag and img_tag.get('src'):
                        image_url = img_tag['src']
                        
                # Use ImageExtractor to validate the RSS image and potentially find better ones
                image_url = self.image_extractor.extract_image(link, html_content=None, feed_image_url=image_url)
                
                import calendar
                published_at = datetime.utcnow()
                if 'published_parsed' in entry and entry.published_parsed:
                    published_at = datetime.utcfromtimestamp(calendar.timegm(entry.published_parsed))

                articles.append({
                    "title": title,
                    "url": link,
                    "image_url": image_url,
                    "published_at": published_at,
                    "content": entry.get('description', '')
                })
        except Exception as e:
            logger.error(f"Error processing RSS for {source.name}: {e}")
        return articles

    def process_json_api(self, source: NewsSource) -> List[Dict[str, Any]]:
        articles = []
        try:
            response = self.fetch_with_backoff(source.url)
            data = response.json()
            
            # Simple heuristic for JSON APIs (assuming articles are in a list)
            items = data if isinstance(data, list) else data.get('articles', data.get('items', []))
            for item in items:
                link = item.get('url', item.get('link', ''))
                title = item.get('title', '')
                if not link or not title:
                    continue
                
                pub_date = datetime.utcnow() # simplified
                
                feed_image_url = item.get('image', item.get('urlToImage'))
                image_url = self.image_extractor.extract_image(link, html_content=None, feed_image_url=feed_image_url)
                
                articles.append({
                    "title": title,
                    "url": link,
                    "image_url": image_url,
                    "published_at": pub_date,
                    "content": item.get('description', item.get('content', ''))
                })
        except Exception as e:
            logger.error(f"Error processing JSON for {source.name}: {e}")
        return articles

    def process_sitemap(self, source: NewsSource) -> List[Dict[str, Any]]:
        articles = []
        try:
            response = self.fetch_with_backoff(source.url)
            soup = BeautifulSoup(response.content, 'lxml-xml')
            
            urls = soup.find_all('url')
            for url_node in urls:
                loc = url_node.find('loc')
                if not loc:
                    continue
                
                link = loc.text
                title = link.split('/')[-1].replace('-', ' ') # Basic title extraction from URL
                
                # Filter out obvious non-article pages
                if "category" in link or "tag" in link:
                    continue
                    
                image_url = self.image_extractor.extract_image(link)
                    
                articles.append({
                    "title": title,
                    "url": link,
                    "image_url": image_url,
                    "published_at": datetime.utcnow(),
                    "content": ""
                })
        except Exception as e:
            logger.error(f"Error processing Sitemap for {source.name}: {e}")
        return articles

    def fetch_source(self, source: NewsSource):
        logger.info(f"Fetching source: {source.name} [{source.type}]")
        
        extracted_data = []
        source_type = source.type.lower()
        
        if 'rss' in source_type or 'xml' in source_type:
            extracted_data = self.process_rss(source)
        elif 'api' in source_type or 'json' in source_type:
            extracted_data = self.process_json_api(source)
        elif 'sitemap' in source_type:
            extracted_data = self.process_sitemap(source)
        else:
            logger.warning(f"Unknown source type: {source_type} for {source.name}, defaulting to RSS.")
            extracted_data = self.process_rss(source)

        return extracted_data

    def run(self):
        active_sources = self.db.query(NewsSource).filter(NewsSource.is_active == True).all()
        logger.info(f"Starting UnifiedNewsCollector for {len(active_sources)} sources.")
        
        total_new_articles = 0
        
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            future_to_source = {
                executor.submit(self.fetch_source, source): source for source in active_sources
            }
            
            for future in as_completed(future_to_source):
                source = future_to_source[future]
                try:
                    extracted_data = future.result()
                    new_articles = []
                    source_type = source.type.lower()
                    
                    for data in extracted_data:
                        if self.deduplicator.is_duplicate(data['title'], data['url'], data['content']):
                            continue
                            
                        language = "hi" if "hindi" in source_type or "hindi" in source.name.lower() else "en"
                        
                        article = NewsArticle(
                            title=data['title'],
                            source_url=data['url'],
                            source_id=source.id,
                            state=source.state,
                            district=source.district,
                            category=source.category,
                            department=source.department,
                            published_at=data['published_at'],
                            status="pending",
                            image_url=data['image_url'],
                            language=language
                        )
                        new_articles.append(article)

                    if new_articles:
                        self.db.add_all(new_articles)
                        self.db.commit() # Commit per source to prevent massive rollbacks
                        total_new_articles += len(new_articles)
                        logger.info(f"Saved {len(new_articles)} new articles from {source.name}.")
                except Exception as exc:
                    logger.error(f"{source.name} generated an exception: {exc}")
                    self.db.rollback()
                    
        return f"UnifiedNewsCollector finished. Total new articles: {total_new_articles}"
