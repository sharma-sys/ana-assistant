import sqlite3


def run():
    conn = sqlite3.connect("ana.db")
    cursor = conn.cursor()

    # 1. Update existing 'National' sources where category is None
    # Aaj Tak, India TV, TV9, BBC, DW, OneIndia, NDTV India, The Hindu, News18 India, Zee News, NDTV Khabar, ABP News, News18 Hindi, Dainik Bhaskar, Lallantop
    national_ids = [13, 14, 15, 16, 17, 18, 24, 25, 26, 27, 28, 30, 31, 46, 47, 48]
    for nid in national_ids:
        cursor.execute(
            "UPDATE news_sources SET category = 'National' WHERE id = ?;", (nid,)
        )

    # 2. Add International sources
    international_sources = [
        (
            "BBC Hindi International",
            "rss",
            "https://feeds.bbci.co.uk/hindi/international/rss.xml",
            "National",
            "International",
        ),
        (
            "Aaj Tak International",
            "rss",
            "https://www.aajtak.in/rssfeeds/?id=international",
            "National",
            "International",
        ),
        (
            "News18 International Hindi",
            "rss",
            "https://hindi.news18.com/rss/khabar/world/world.xml",
            "National",
            "International",
        ),
    ]
    for name, type, url, state, cat in international_sources:
        cursor.execute(
            "INSERT OR IGNORE INTO news_sources (name, type, url, state, category, is_active) VALUES (?, ?, ?, ?, ?, 1)",
            (name, type, url, state, cat),
        )

    # 3. Add Sports sources
    sports_sources = [
        (
            "Aaj Tak Sports",
            "rss",
            "https://www.aajtak.in/rssfeeds/?id=sports",
            "National",
            "Sports",
        ),
        (
            "News18 Sports Hindi",
            "rss",
            "https://hindi.news18.com/rss/khabar/sports/sports.xml",
            "National",
            "Sports",
        ),
        (
            "Zee News Sports Hindi",
            "rss",
            "https://zeenews.india.com/hindi/sports/rss",
            "National",
            "Sports",
        ),
    ]
    for name, type, url, state, cat in sports_sources:
        cursor.execute(
            "INSERT OR IGNORE INTO news_sources (name, type, url, state, category, is_active) VALUES (?, ?, ?, ?, ?, 1)",
            (name, type, url, state, cat),
        )

    # Set remaining None categories to 'General'
    cursor.execute(
        "UPDATE news_sources SET category = 'General' WHERE category IS NULL;"
    )

    # Also update articles based on source
    cursor.execute("""
        UPDATE news_articles 
        SET category = (
            SELECT category FROM news_sources WHERE news_sources.id = news_articles.source_id
        )
        WHERE category IS NULL;
    """)

    conn.commit()
    conn.close()
    print("Database updated with new categories and sources.")


if __name__ == "__main__":
    run()
