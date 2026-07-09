import sqlite3
import sys

# Seed script for Government Hindi News Feeds (Using Google News aggregations to guarantee .gov.in/.nic.in/PIB validity)

gov_publishers = [
    # PIB (Press Information Bureau)
    {
        "name": "PIB Hindi",
        "url": "https://news.google.com/rss/search?q=PIB+hindi&hl=hi&gl=IN&ceid=IN:hi",
        "state": "National",
        "district": None,
    },
    # State Gov
    {
        "name": "UP Govt Announcements",
        "url": "https://news.google.com/rss/search?q=site:up.gov.in+hindi&hl=hi&gl=IN&ceid=IN:hi",
        "state": "Uttar Pradesh",
        "district": None,
    },
    {
        "name": "MP Govt Announcements",
        "url": "https://news.google.com/rss/search?q=site:mp.gov.in+hindi&hl=hi&gl=IN&ceid=IN:hi",
        "state": "Madhya Pradesh",
        "district": None,
    },
    {
        "name": "Bihar Govt Announcements",
        "url": "https://news.google.com/rss/search?q=site:bihar.gov.in+hindi&hl=hi&gl=IN&ceid=IN:hi",
        "state": "Bihar",
        "district": None,
    },
    {
        "name": "Rajasthan Govt Announcements",
        "url": "https://news.google.com/rss/search?q=site:rajasthan.gov.in+hindi&hl=hi&gl=IN&ceid=IN:hi",
        "state": "Rajasthan",
        "district": None,
    },
    # National Gov Portals
    {
        "name": "India Govt Announcements",
        "url": "https://news.google.com/rss/search?q=site:india.gov.in+hindi&hl=hi&gl=IN&ceid=IN:hi",
        "state": "National",
        "district": None,
    },
    {
        "name": "PMIndia Hindi",
        "url": "https://news.google.com/rss/search?q=site:pmindia.gov.in+hindi&hl=hi&gl=IN&ceid=IN:hi",
        "state": "National",
        "district": None,
    },
]


def main():
    try:
        conn = sqlite3.connect("ana.db")
        c = conn.cursor()

        inserted = 0
        for pub in gov_publishers:
            c.execute("SELECT id FROM news_sources WHERE url=?", (pub["url"],))
            exists = c.fetchone()

            if not exists:
                c.execute(
                    "INSERT INTO news_sources (name, type, url, state, district, is_active) VALUES (?, ?, ?, ?, ?, ?)",
                    (
                        pub["name"],
                        "rss_gov",
                        pub["url"],
                        pub["state"],
                        pub["district"],
                        1,
                    ),
                )
                inserted += 1

        conn.commit()
        print(f"Successfully added {inserted} new government publishers.")
    except Exception as e:
        print(f"Error adding government publishers: {e}")
        sys.exit(1)
    finally:
        if "conn" in locals():
            conn.close()


if __name__ == "__main__":
    main()
