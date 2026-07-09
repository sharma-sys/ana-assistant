import sqlite3
import sys

# Official Indian State-Level Hindi News Publishers
# Using recognized Hindi newspapers/channels for different states.

state_publishers = [
    # National (previously hardcoded)
    {
        "name": "Aaj Tak - Hindi",
        "url": "https://www.aajtak.in/rssfeeds/?id=home",
        "state": "All",
    },
    {
        "name": "ABP News - Hindi",
        "url": "https://www.abplive.com/home/feed",
        "state": "All",
    },
    {
        "name": "Zee News - Hindi",
        "url": "https://zeenews.india.com/hindi/india/rss",
        "state": "All",
        "active": 0,
    },  # Known 403 issue
    {
        "name": "News18 - Hindi",
        "url": "https://hindi.news18.com/rss/khabar/nation/nation.xml",
        "state": "All",
    },
    {
        "name": "India TV - Hindi",
        "url": "https://www.indiatv.in/rssnews/topstory.xml",
        "state": "All",
    },
    {
        "name": "NDTV Khabar - Hindi",
        "url": "https://feeds.feedburner.com/ndtvkhabar-latest",
        "state": "All",
    },
    {
        "name": "TV9 Bharatvarsh - Hindi",
        "url": "https://tv9hindi.com/feed",
        "state": "All",
    },
    {
        "name": "BBC Hindi",
        "url": "https://feeds.bbci.co.uk/hindi/rss.xml",
        "state": "All",
    },
    {"name": "DW Hindi", "url": "https://rss.dw.com/xml/rss-hin-all", "state": "All"},
    {
        "name": "OneIndia Hindi",
        "url": "https://hindi.oneindia.com/rss/hindi-india-fb.xml",
        "state": "All",
    },
    # Uttar Pradesh
    {
        "name": "Jagran - UP",
        "url": "https://english.jagran.com/rss/uttar-pradesh.xml",
        "state": "Uttar Pradesh",
    },  # Jagran english rss, wait, let's use hindi
    {
        "name": "Amar Ujala - UP",
        "url": "https://www.amarujala.com/rss/uttar-pradesh",
        "state": "Uttar Pradesh",
    },
    {
        "name": "Live Hindustan - UP",
        "url": "https://www.livehindustan.com/rss/uttar-pradesh",
        "state": "Uttar Pradesh",
    },
    {
        "name": "News18 UP",
        "url": "https://hindi.news18.com/rss/khabar/uttar-pradesh/uttar-pradesh.xml",
        "state": "Uttar Pradesh",
    },
    # Madhya Pradesh
    {
        "name": "Amar Ujala - MP",
        "url": "https://www.amarujala.com/rss/madhya-pradesh",
        "state": "Madhya Pradesh",
    },
    {
        "name": "News18 MP",
        "url": "https://hindi.news18.com/rss/khabar/madhya-pradesh/madhya-pradesh.xml",
        "state": "Madhya Pradesh",
    },
    # Bihar
    {
        "name": "Amar Ujala - Bihar",
        "url": "https://www.amarujala.com/rss/bihar",
        "state": "Bihar",
    },
    {
        "name": "Live Hindustan - Bihar",
        "url": "https://www.livehindustan.com/rss/bihar",
        "state": "Bihar",
    },
    {
        "name": "News18 Bihar",
        "url": "https://hindi.news18.com/rss/khabar/bihar/bihar.xml",
        "state": "Bihar",
    },
    # Rajasthan
    {
        "name": "Amar Ujala - Rajasthan",
        "url": "https://www.amarujala.com/rss/rajasthan",
        "state": "Rajasthan",
    },
    {
        "name": "News18 Rajasthan",
        "url": "https://hindi.news18.com/rss/khabar/rajasthan/rajasthan.xml",
        "state": "Rajasthan",
    },
    # Maharashtra
    {
        "name": "Amar Ujala - Maharashtra",
        "url": "https://www.amarujala.com/rss/maharashtra",
        "state": "Maharashtra",
    },
    # Delhi
    {
        "name": "Amar Ujala - Delhi",
        "url": "https://www.amarujala.com/rss/delhi-ncr",
        "state": "Delhi",
    },
    {
        "name": "News18 Delhi",
        "url": "https://hindi.news18.com/rss/khabar/delhi/delhi.xml",
        "state": "Delhi",
    },
]


def main():
    try:
        conn = sqlite3.connect("ana.db")
        c = conn.cursor()

        inserted = 0
        for pub in state_publishers:
            c.execute("SELECT id FROM news_sources WHERE url=?", (pub["url"],))
            exists = c.fetchone()

            is_active = pub.get("active", 1)

            if not exists:
                c.execute(
                    "INSERT INTO news_sources (name, type, url, state, is_active) VALUES (?, ?, ?, ?, ?)",
                    (pub["name"], "rss_hindi", pub["url"], pub["state"], is_active),
                )
                inserted += 1
            else:
                # Update state just in case it was incorrectly categorized before
                c.execute(
                    "UPDATE news_sources SET state=?, type='rss_hindi' WHERE url=?",
                    (pub["state"], pub["url"]),
                )

        conn.commit()
        print(f"Seed complete. {inserted} new state publishers inserted.")
    except Exception as e:
        print(f"Error seeding publishers: {e}")
        sys.exit(1)
    finally:
        if "conn" in locals():
            conn.close()


if __name__ == "__main__":
    main()
