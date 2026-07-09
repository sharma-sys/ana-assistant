import sqlite3
import sys

district_publishers = [
    # Uttar Pradesh
    {
        "name": "Lucknow Local News",
        "url": "https://news.google.com/rss/search?q=Lucknow+news+hindi&hl=hi&gl=IN&ceid=IN:hi",
        "state": "Uttar Pradesh",
        "district": "Lucknow",
    },
    {
        "name": "Kanpur Local News",
        "url": "https://news.google.com/rss/search?q=Kanpur+news+hindi&hl=hi&gl=IN&ceid=IN:hi",
        "state": "Uttar Pradesh",
        "district": "Kanpur",
    },
    {
        "name": "Varanasi Local News",
        "url": "https://news.google.com/rss/search?q=Varanasi+news+hindi&hl=hi&gl=IN&ceid=IN:hi",
        "state": "Uttar Pradesh",
        "district": "Varanasi",
    },
    {
        "name": "Agra Local News",
        "url": "https://news.google.com/rss/search?q=Agra+news+hindi&hl=hi&gl=IN&ceid=IN:hi",
        "state": "Uttar Pradesh",
        "district": "Agra",
    },
    # Madhya Pradesh
    {
        "name": "Bhopal Local News",
        "url": "https://news.google.com/rss/search?q=Bhopal+news+hindi&hl=hi&gl=IN&ceid=IN:hi",
        "state": "Madhya Pradesh",
        "district": "Bhopal",
    },
    {
        "name": "Indore Local News",
        "url": "https://news.google.com/rss/search?q=Indore+news+hindi&hl=hi&gl=IN&ceid=IN:hi",
        "state": "Madhya Pradesh",
        "district": "Indore",
    },
    {
        "name": "Gwalior Local News",
        "url": "https://news.google.com/rss/search?q=Gwalior+news+hindi&hl=hi&gl=IN&ceid=IN:hi",
        "state": "Madhya Pradesh",
        "district": "Gwalior",
    },
    # Bihar
    {
        "name": "Patna Local News",
        "url": "https://news.google.com/rss/search?q=Patna+news+hindi&hl=hi&gl=IN&ceid=IN:hi",
        "state": "Bihar",
        "district": "Patna",
    },
    {
        "name": "Muzaffarpur Local News",
        "url": "https://news.google.com/rss/search?q=Muzaffarpur+news+hindi&hl=hi&gl=IN&ceid=IN:hi",
        "state": "Bihar",
        "district": "Muzaffarpur",
    },
    # Rajasthan
    {
        "name": "Jaipur Local News",
        "url": "https://news.google.com/rss/search?q=Jaipur+news+hindi&hl=hi&gl=IN&ceid=IN:hi",
        "state": "Rajasthan",
        "district": "Jaipur",
    },
    {
        "name": "Jodhpur Local News",
        "url": "https://news.google.com/rss/search?q=Jodhpur+news+hindi&hl=hi&gl=IN&ceid=IN:hi",
        "state": "Rajasthan",
        "district": "Jodhpur",
    },
    # Maharashtra
    {
        "name": "Mumbai Local News",
        "url": "https://news.google.com/rss/search?q=Mumbai+news+hindi&hl=hi&gl=IN&ceid=IN:hi",
        "state": "Maharashtra",
        "district": "Mumbai",
    },
]


def main():
    try:
        conn = sqlite3.connect("ana.db")
        c = conn.cursor()

        # Cleanup old broken amar ujala ones
        c.execute(
            "DELETE FROM news_articles WHERE source_id IN (SELECT id FROM news_sources WHERE url LIKE '%amarujala.com/rss%')"
        )
        c.execute("DELETE FROM news_sources WHERE url LIKE '%amarujala.com/rss%'")

        inserted = 0
        for pub in district_publishers:
            c.execute("SELECT id FROM news_sources WHERE url=?", (pub["url"],))
            exists = c.fetchone()

            if not exists:
                c.execute(
                    "INSERT INTO news_sources (name, type, url, state, district, is_active) VALUES (?, ?, ?, ?, ?, ?)",
                    (
                        pub["name"],
                        "rss_district",
                        pub["url"],
                        pub["state"],
                        pub["district"],
                        1,
                    ),
                )
                inserted += 1

        conn.commit()
        print(f"Successfully added {inserted} new district publishers.")
    except Exception as e:
        print(f"Error adding district publishers: {e}")
        sys.exit(1)
    finally:
        if "conn" in locals():
            conn.close()


if __name__ == "__main__":
    main()
