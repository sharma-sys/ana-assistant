"""
Seed script: Add rss_district sources to NeonDB (production backend).
Run with: python seed_district_sources.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from database.session import SessionLocal
from database.models import NewsSource

DISTRICT_SOURCES = [
    # Madhya Pradesh
    {"name": "Bhopal Local News",      "state": "Madhya Pradesh", "district": "Bhopal",      "url": "https://news.google.com/rss/search?q=Bhopal+news+hindi&hl=hi&gl=IN&ceid=IN:hi"},
    {"name": "Indore Local News",      "state": "Madhya Pradesh", "district": "Indore",      "url": "https://news.google.com/rss/search?q=Indore+news+hindi&hl=hi&gl=IN&ceid=IN:hi"},
    {"name": "Gwalior Local News",     "state": "Madhya Pradesh", "district": "Gwalior",     "url": "https://news.google.com/rss/search?q=Gwalior+news+hindi&hl=hi&gl=IN&ceid=IN:hi"},
    {"name": "Jabalpur Local News",    "state": "Madhya Pradesh", "district": "Jabalpur",    "url": "https://news.google.com/rss/search?q=Jabalpur+news+hindi&hl=hi&gl=IN&ceid=IN:hi"},
    {"name": "Ujjain Local News",      "state": "Madhya Pradesh", "district": "Ujjain",      "url": "https://news.google.com/rss/search?q=Ujjain+news+hindi&hl=hi&gl=IN&ceid=IN:hi"},
    # Uttar Pradesh
    {"name": "Lucknow Local News",     "state": "Uttar Pradesh",  "district": "Lucknow",     "url": "https://news.google.com/rss/search?q=Lucknow+news+hindi&hl=hi&gl=IN&ceid=IN:hi"},
    {"name": "Kanpur Local News",      "state": "Uttar Pradesh",  "district": "Kanpur",      "url": "https://news.google.com/rss/search?q=Kanpur+news+hindi&hl=hi&gl=IN&ceid=IN:hi"},
    {"name": "Varanasi Local News",    "state": "Uttar Pradesh",  "district": "Varanasi",    "url": "https://news.google.com/rss/search?q=Varanasi+news+hindi&hl=hi&gl=IN&ceid=IN:hi"},
    {"name": "Agra Local News",        "state": "Uttar Pradesh",  "district": "Agra",        "url": "https://news.google.com/rss/search?q=Agra+news+hindi&hl=hi&gl=IN&ceid=IN:hi"},
    {"name": "Meerut Local News",      "state": "Uttar Pradesh",  "district": "Meerut",      "url": "https://news.google.com/rss/search?q=Meerut+news+hindi&hl=hi&gl=IN&ceid=IN:hi"},
    # Bihar
    {"name": "Patna Local News",       "state": "Bihar",           "district": "Patna",       "url": "https://news.google.com/rss/search?q=Patna+news+hindi&hl=hi&gl=IN&ceid=IN:hi"},
    {"name": "Muzaffarpur Local News", "state": "Bihar",           "district": "Muzaffarpur", "url": "https://news.google.com/rss/search?q=Muzaffarpur+news+hindi&hl=hi&gl=IN&ceid=IN:hi"},
    {"name": "Gaya Local News",        "state": "Bihar",           "district": "Gaya",        "url": "https://news.google.com/rss/search?q=Gaya+news+hindi&hl=hi&gl=IN&ceid=IN:hi"},
    # Rajasthan
    {"name": "Jaipur Local News",      "state": "Rajasthan",       "district": "Jaipur",      "url": "https://news.google.com/rss/search?q=Jaipur+news+hindi&hl=hi&gl=IN&ceid=IN:hi"},
    {"name": "Jodhpur Local News",     "state": "Rajasthan",       "district": "Jodhpur",     "url": "https://news.google.com/rss/search?q=Jodhpur+news+hindi&hl=hi&gl=IN&ceid=IN:hi"},
    {"name": "Udaipur Local News",     "state": "Rajasthan",       "district": "Udaipur",     "url": "https://news.google.com/rss/search?q=Udaipur+news+hindi&hl=hi&gl=IN&ceid=IN:hi"},
    # Maharashtra
    {"name": "Mumbai Local News",      "state": "Maharashtra",     "district": "Mumbai",      "url": "https://news.google.com/rss/search?q=Mumbai+news+hindi&hl=hi&gl=IN&ceid=IN:hi"},
    {"name": "Pune Local News",        "state": "Maharashtra",     "district": "Pune",        "url": "https://news.google.com/rss/search?q=Pune+news+hindi&hl=hi&gl=IN&ceid=IN:hi"},
    {"name": "Nagpur Local News",      "state": "Maharashtra",     "district": "Nagpur",      "url": "https://news.google.com/rss/search?q=Nagpur+news+hindi&hl=hi&gl=IN&ceid=IN:hi"},
    # Delhi
    {"name": "Delhi Local News",       "state": "Delhi",           "district": "Delhi",       "url": "https://news.google.com/rss/search?q=Delhi+news+hindi&hl=hi&gl=IN&ceid=IN:hi"},
]

def main():
    db = SessionLocal()
    added = 0
    skipped = 0
    try:
        for src_data in DISTRICT_SOURCES:
            existing = db.query(NewsSource).filter(NewsSource.url == src_data["url"]).first()
            if existing:
                print(f"  SKIP (exists): {src_data['name']}")
                skipped += 1
                continue
            source = NewsSource(
                name=src_data["name"],
                type="rss_district",
                url=src_data["url"],
                state=src_data["state"],
                district=src_data["district"],
                category="Regional",
                is_active=True,
            )
            db.add(source)
            added += 1
            print(f"  ADDED: {src_data['name']} ({src_data['state']} > {src_data['district']})")
        db.commit()
        print(f"\nDone! Added {added}, Skipped {skipped}")
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    main()
