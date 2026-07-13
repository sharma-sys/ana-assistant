import os
import sys
import logging
import requests
from bs4 import BeautifulSoup
import feedparser
from urllib.parse import urlparse

# Ensure backend directory is in path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database.session import SessionLocal
from database.models import NewsSource

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

HINDI_SOURCES = [
    # National
    {"name": "Amar Ujala", "url": "https://www.amarujala.com/", "category": "National", "state": "National"},
    {"name": "Live Hindustan", "url": "https://www.livehindustan.com/", "category": "National", "state": "National"},
    {"name": "News18 Hindi", "url": "https://hindi.news18.com/", "category": "National", "state": "National"},
    {"name": "ABP News Hindi", "url": "https://www.abplive.com/", "category": "National", "state": "National"},
    {"name": "Aaj Tak", "url": "https://www.aajtak.in/", "category": "National", "state": "National"},
    {"name": "NDTV India", "url": "https://ndtv.in/", "category": "National", "state": "National"},
    {"name": "TV9 Bharatvarsh", "url": "https://www.tv9hindi.com/", "category": "National", "state": "National"},
    {"name": "Zee News Hindi", "url": "https://zeenews.india.com/hindi", "category": "National", "state": "National"},
    {"name": "Navbharat Times", "url": "https://navbharattimes.indiatimes.com/", "category": "National", "state": "National"},
    {"name": "India TV Hindi", "url": "https://www.indiatv.in/", "category": "National", "state": "National"},
    {"name": "Jansatta Hindi", "url": "https://www.jansatta.com/", "category": "National", "state": "National"},
    {"name": "Punjab Kesari", "url": "https://www.punjabkesari.in/", "category": "National", "state": "National"},
    {"name": "Prabhat Khabar", "url": "https://www.prabhatkhabar.com/", "category": "National", "state": "National"},
    {"name": "Haribhoomi", "url": "https://www.haribhoomi.com/", "category": "National", "state": "National"},
    {"name": "Webdunia Hindi", "url": "https://hindi.webdunia.com/", "category": "National", "state": "National"},

    # State & Regional
    {"name": "Rajasthan Tak", "url": "https://rajasthan.tak.live/", "category": "Regional", "state": "Rajasthan"},
    {"name": "MP Breaking News", "url": "https://mpbreakingnews.in/", "category": "Regional", "state": "Madhya Pradesh"},
    {"name": "ETV Bharat Hindi", "url": "https://www.etvbharat.com/hindi/national", "category": "Regional", "state": "Multiple"},
    {"name": "Khabar Lahariya", "url": "https://khabarlahariya.org/", "category": "Regional", "state": "Uttar Pradesh"},
    {"name": "First Bihar Jharkhand", "url": "https://firstbihar.com/", "category": "Regional", "state": "Bihar"},
    {"name": "Chhattisgarh Today", "url": "https://chhattisgarhtoday.in/", "category": "Regional", "state": "Chhattisgarh"},
    {"name": "Bihar Tak", "url": "https://bihar.tak.live/", "category": "Regional", "state": "Bihar"},
    {"name": "UP Tak", "url": "https://up.tak.live/", "category": "Regional", "state": "Uttar Pradesh"},
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
}

def get_domain(url):
    try:
        return urlparse(url).netloc.replace("www.", "")
    except:
        return url

def validate_rss(rss_url):
    try:
        response = requests.get(rss_url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        feed = feedparser.parse(response.content)
        if feed.entries and len(feed.entries) > 0:
            return True
    except Exception as e:
        logger.debug(f"RSS Validation failed for {rss_url}: {e}")
    return False

def discover_rss(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Look for RSS link tags
        rss_links = soup.find_all("link", type=["application/rss+xml", "application/atom+xml"])
        for link in rss_links:
            href = link.get("href")
            if href:
                if href.startswith("/"):
                    from urllib.parse import urljoin
                    href = urljoin(url, href)
                if validate_rss(href):
                    return href
    except Exception as e:
        logger.debug(f"RSS Discovery failed for {url}: {e}")
    return None

def main():
    db = SessionLocal()
    
    total_before = db.query(NewsSource).count()
    
    added_sources = []
    skipped_duplicates = []
    skipped_restrictions = []
    
    existing_sources = db.query(NewsSource).all()
    existing_urls = [s.url.lower() for s in existing_sources if s.url]
    existing_names = [s.name.lower() for s in existing_sources if s.name]
    existing_domains = [get_domain(u) for u in existing_urls]
    
    for src in HINDI_SOURCES:
        logger.info(f"Processing: {src['name']} ({src['url']})")
        
        domain = get_domain(src['url'])
        
        # Check duplicate
        if src['name'].lower() in existing_names or src['url'].lower() in existing_urls or domain in existing_domains:
            logger.info(f"  -> Skipped: Duplicate source found.")
            skipped_duplicates.append(src)
            continue
            
        # Discover RSS
        rss_url = discover_rss(src['url'])
        final_url = None
        final_type = None
        
        if rss_url:
            logger.info(f"  -> Found RSS: {rss_url}")
            final_url = rss_url
            final_type = f"rss_{src['category'].lower()}"
        else:
            logger.info(f"  -> No RSS found. Checking website accessibility...")
            try:
                # Check accessibility for scraper
                response = requests.get(src['url'], headers=HEADERS, timeout=10)
                response.raise_for_status()
                logger.info(f"  -> Website accessible. Configuring as scraper.")
                final_url = src['url']
                final_type = f"scraper_{src['category'].lower()}"
            except Exception as e:
                logger.warning(f"  -> Skipped: Blocked/Paywalled/Inaccessible. Reason: {e}")
                src['reason'] = str(e)
                skipped_restrictions.append(src)
                continue
                
        if final_url and final_type:
            new_source = NewsSource(
                name=src['name'],
                type=final_type,
                url=final_url,
                state=src['state'],
                category=src['category'],
                is_active=True
            )
            db.add(new_source)
            # Add to local lists to prevent duplicates in the same run if any
            existing_names.append(src['name'].lower())
            existing_urls.append(final_url.lower())
            existing_domains.append(get_domain(final_url))
            
            src['final_url'] = final_url
            src['final_type'] = final_type
            added_sources.append(src)
            
    try:
        db.commit()
    except Exception as e:
        logger.error(f"Failed to commit to database: {e}")
        db.rollback()
        
    total_after = db.query(NewsSource).count()
    db.close()
    
    # Generate Markdown Report
    report_path = os.path.join(os.path.dirname(__file__), "..", "..", "ANA_HINDI_SOURCES_AUDIT.md")
    report_path = os.path.abspath(report_path)
    
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# ANA Hindi News Sources Audit Report\n\n")
        f.write("## Overview\n")
        f.write(f"- **Total sources before execution:** {total_before}\n")
        f.write(f"- **Total sources after execution:** {total_after}\n")
        f.write(f"- **Net sources added:** {len(added_sources)}\n\n")
        
        f.write("## Newly Added Sources\n")
        if added_sources:
            for s in added_sources:
                f.write(f"- **{s['name']}** ({s['category']} - {s['state']})\n")
                f.write(f"  - Config Type: `{s['final_type']}`\n")
                f.write(f"  - URL: {s['final_url']}\n")
        else:
            f.write("- None\n")
            
        f.write("\n## Skipped Duplicate Sources\n")
        if skipped_duplicates:
            for s in skipped_duplicates:
                f.write(f"- **{s['name']}** ({s['url']})\n")
        else:
            f.write("- None\n")
            
        f.write("\n## Sources Skipped Due to Restrictions (No RSS & Blocked Scraper)\n")
        if skipped_restrictions:
            for s in skipped_restrictions:
                f.write(f"- **{s['name']}** ({s['url']})\n")
                f.write(f"  - Reason: `{s['reason']}`\n")
        else:
            f.write("- None\n")
            
    logger.info(f"Audit report generated at: {report_path}")

if __name__ == "__main__":
    main()
