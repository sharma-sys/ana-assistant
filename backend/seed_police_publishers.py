import sqlite3
import sys

# Seed script for Police Hindi News Feeds (Using Google News aggregations to ensure official domain/topic coverage)

police_publishers = [
    # State Police
    {
        "name": "UP Police News",
        "url": "https://news.google.com/rss/search?q=UP+Police+news+hindi&hl=hi&gl=IN&ceid=IN:hi",
        "state": "Uttar Pradesh",
        "district": None,
        "department": "State Police",
    },
    {
        "name": "MP Police News",
        "url": "https://news.google.com/rss/search?q=MP+Police+news+hindi&hl=hi&gl=IN&ceid=IN:hi",
        "state": "Madhya Pradesh",
        "district": None,
        "department": "State Police",
    },
    {
        "name": "Bihar Police News",
        "url": "https://news.google.com/rss/search?q=Bihar+Police+news+hindi&hl=hi&gl=IN&ceid=IN:hi",
        "state": "Bihar",
        "district": None,
        "department": "State Police",
    },
    # District Police
    {
        "name": "Lucknow Police News",
        "url": "https://news.google.com/rss/search?q=Lucknow+Police+news+hindi&hl=hi&gl=IN&ceid=IN:hi",
        "state": "Uttar Pradesh",
        "district": "Lucknow",
        "department": "District Police",
    },
    {
        "name": "Patna Police News",
        "url": "https://news.google.com/rss/search?q=Patna+Police+news+hindi&hl=hi&gl=IN&ceid=IN:hi",
        "state": "Bihar",
        "district": "Patna",
        "department": "District Police",
    },
    {
        "name": "Indore Police News",
        "url": "https://news.google.com/rss/search?q=Indore+Police+news+hindi&hl=hi&gl=IN&ceid=IN:hi",
        "state": "Madhya Pradesh",
        "district": "Indore",
        "department": "District Police",
    },
    # Traffic Police
    {
        "name": "Delhi Traffic Police Alerts",
        "url": "https://news.google.com/rss/search?q=Delhi+Traffic+Police+hindi&hl=hi&gl=IN&ceid=IN:hi",
        "state": "Delhi",
        "district": None,
        "department": "Traffic Police",
    },
    {
        "name": "Mumbai Traffic Police Alerts",
        "url": "https://news.google.com/rss/search?q=Mumbai+Traffic+Police+hindi&hl=hi&gl=IN&ceid=IN:hi",
        "state": "Maharashtra",
        "district": "Mumbai",
        "department": "Traffic Police",
    },
    {
        "name": "UP Traffic Police Alerts",
        "url": "https://news.google.com/rss/search?q=UP+Traffic+Police+hindi&hl=hi&gl=IN&ceid=IN:hi",
        "state": "Uttar Pradesh",
        "district": None,
        "department": "Traffic Police",
    },
    # Cyber Police
    {
        "name": "India Cyber Police Advisory",
        "url": "https://news.google.com/rss/search?q=Cyber+Police+advisory+hindi&hl=hi&gl=IN&ceid=IN:hi",
        "state": "National",
        "district": None,
        "department": "Cyber Police",
    },
    {
        "name": "UP Cyber Crime News",
        "url": "https://news.google.com/rss/search?q=UP+Cyber+Crime+Police+hindi&hl=hi&gl=IN&ceid=IN:hi",
        "state": "Uttar Pradesh",
        "district": None,
        "department": "Cyber Police",
    },
]


def main():
    try:
        conn = sqlite3.connect("ana.db")
        c = conn.cursor()

        inserted = 0
        for pub in police_publishers:
            c.execute("SELECT id FROM news_sources WHERE url=?", (pub["url"],))
            exists = c.fetchone()

            if not exists:
                c.execute(
                    "INSERT INTO news_sources (name, type, url, state, district, department, is_active) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (
                        pub["name"],
                        "rss_police",
                        pub["url"],
                        pub["state"],
                        pub["district"],
                        pub["department"],
                        1,
                    ),
                )
                inserted += 1

        conn.commit()
        print(f"Successfully added {inserted} new police publishers.")
    except Exception as e:
        print(f"Error adding police publishers: {e}")
        sys.exit(1)
    finally:
        if "conn" in locals():
            conn.close()


if __name__ == "__main__":
    main()
