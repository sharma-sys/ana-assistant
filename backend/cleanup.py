import sqlite3

conn = sqlite3.connect("ana.db")
c = conn.cursor()
c.execute(
    "DELETE FROM news_articles WHERE source_id IN (SELECT id FROM news_sources WHERE type != 'rss_hindi')"
)
c.execute("DELETE FROM news_sources WHERE type != 'rss_hindi'")
conn.commit()
print("Cleaned non-Hindi records")
conn.close()
