import sqlite3
import sys


def main():
    try:
        conn = sqlite3.connect("ana.db")
        c = conn.cursor()

        publishers = [
            {
                "name": "Dainik Bhaskar",
                "url": "https://news.google.com/rss/search?q=site:bhaskar.com&hl=hi&gl=IN&ceid=IN:hi",
                "state": "All",
            },
            {
                "name": "The Lallantop",
                "url": "https://news.google.com/rss/search?q=site:thelallantop.com&hl=hi&gl=IN&ceid=IN:hi",
                "state": "All",
            },
        ]

        inserted = 0
        for pub in publishers:
            c.execute("SELECT id FROM news_sources WHERE url=?", (pub["url"],))
            exists = c.fetchone()

            if not exists:
                c.execute(
                    "INSERT INTO news_sources (name, type, url, state, is_active) VALUES (?, ?, ?, ?, ?)",
                    (pub["name"], "rss_hindi", pub["url"], pub["state"], 1),
                )
                inserted += 1

        conn.commit()
        print(f"Successfully added {inserted} new national publishers.")
    except Exception as e:
        print(f"Error adding publishers: {e}")
        sys.exit(1)
    finally:
        if "conn" in locals():
            conn.close()


if __name__ == "__main__":
    main()
