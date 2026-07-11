"""Debug district collector step by step."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import cloudscraper
import feedparser
from database.session import SessionLocal
from database.models import NewsSource, NewsArticle

db = SessionLocal()

# Get Bhopal source
source = db.query(NewsSource).filter(NewsSource.district == "Bhopal").first()
print(f"Source: {source.name}, URL: {source.url}")

# Fetch feed
scraper = cloudscraper.create_scraper(browser={"browser":"chrome","platform":"windows","mobile":False})
res = scraper.get(source.url, timeout=15)
print(f"HTTP Status: {res.status_code}, Length: {len(res.text)}")

# Parse
feed = feedparser.parse(res.text)
print(f"Feed entries: {len(feed.entries)}")

if feed.entries:
    entry = feed.entries[0]
    print(f"\nFirst entry:")
    print(f"  title: {entry.get('title', 'N/A')}")
    print(f"  link: {entry.get('link', 'N/A')}")
    print(f"  has link: {hasattr(entry, 'link')}")

    # Check deduplicate
    from collectors.deduplicator import Deduplicator
    dup = Deduplicator(db)
    is_dup = dup.is_duplicate(entry.get("title",""), entry.link)
    print(f"  is_duplicate: {is_dup}")

    # Try to store directly
    if not is_dup:
        from datetime import datetime
        article = NewsArticle(
            title=entry.get("title","Test"),
            source_url=entry.link,
            source_id=source.id,
            state=source.state,
            district=source.district,
            category=source.category,
            published_at=datetime.utcnow(),
            status="pending",
        )
        db.add(article)
        db.commit()
        print(f"  ✅ Article saved! district={source.district}")
    else:
        print("  Already exists in DB")

# Count existing
count = db.query(NewsArticle).filter(NewsArticle.district=="Bhopal").count()
print(f"\nTotal Bhopal articles in DB: {count}")
db.close()
