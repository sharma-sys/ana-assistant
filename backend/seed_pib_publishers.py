import sqlite3
import sys

pib_publishers = [
    # Press Releases
    {
        "name": "PIB Press Releases Hindi",
        "url": "https://news.google.com/rss/search?q=PIB+Press+Release+hindi&hl=hi&gl=IN&ceid=IN:hi",
        "state": "National",
        "district": None,
        "department": "Press Release",
    },
    # Government Announcements
    {
        "name": "PIB Govt Announcements Hindi",
        "url": "https://news.google.com/rss/search?q=PIB+Government+Announcements+hindi&hl=hi&gl=IN&ceid=IN:hi",
        "state": "National",
        "district": None,
        "department": "Government Announcement",
    },
    # Ministry Updates (A few major ministries)
    {
        "name": "Ministry of Home Affairs Hindi",
        "url": "https://news.google.com/rss/search?q=Ministry+of+Home+Affairs+PIB+hindi&hl=hi&gl=IN&ceid=IN:hi",
        "state": "National",
        "district": None,
        "department": "Ministry Update",
    },
    {
        "name": "Ministry of Finance Hindi",
        "url": "https://news.google.com/rss/search?q=Ministry+of+Finance+PIB+hindi&hl=hi&gl=IN&ceid=IN:hi",
        "state": "National",
        "district": None,
        "department": "Ministry Update",
    },
    {
        "name": "Ministry of Defence Hindi",
        "url": "https://news.google.com/rss/search?q=Ministry+of+Defence+PIB+hindi&hl=hi&gl=IN&ceid=IN:hi",
        "state": "National",
        "district": None,
        "department": "Ministry Update",
    },
    {
        "name": "Ministry of External Affairs Hindi",
        "url": "https://news.google.com/rss/search?q=Ministry+of+External+Affairs+PIB+hindi&hl=hi&gl=IN&ceid=IN:hi",
        "state": "National",
        "district": None,
        "department": "Ministry Update",
    },
    {
        "name": "Ministry of Health Hindi",
        "url": "https://news.google.com/rss/search?q=Ministry+of+Health+PIB+hindi&hl=hi&gl=IN&ceid=IN:hi",
        "state": "National",
        "district": None,
        "department": "Ministry Update",
    },
]


def main():
    try:
        conn = sqlite3.connect("ana.db")
        c = conn.cursor()

        # Remove the generic PIB Hindi added in Phase 4 to avoid duplicates
        c.execute("DELETE FROM news_sources WHERE name='PIB Hindi'")
        print("Removed generic 'PIB Hindi' from Government collector.")

        inserted = 0
        for pub in pib_publishers:
            c.execute("SELECT id FROM news_sources WHERE url=?", (pub["url"],))
            exists = c.fetchone()

            if not exists:
                c.execute(
                    "INSERT INTO news_sources (name, type, url, state, district, department, is_active) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (
                        pub["name"],
                        "rss_pib",
                        pub["url"],
                        pub["state"],
                        pub["district"],
                        pub["department"],
                        1,
                    ),
                )
                inserted += 1

        conn.commit()
        print(f"Successfully added {inserted} specific PIB publishers.")
    except Exception as e:
        print(f"Error adding PIB publishers: {e}")
        sys.exit(1)
    finally:
        if "conn" in locals():
            conn.close()


if __name__ == "__main__":
    main()
