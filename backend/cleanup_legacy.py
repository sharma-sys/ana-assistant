import sqlite3

conn = sqlite3.connect("ana.db")
c = conn.cursor()
c.execute(
    "DELETE FROM news_articles WHERE source_id IN (SELECT id FROM news_sources WHERE url='https://zeenews.india.com/hindi/india/rss' OR url='https://www.tv9hindi.com/national/feed')"
)
c.execute(
    "DELETE FROM news_sources WHERE url='https://zeenews.india.com/hindi/india/rss' OR url='https://www.tv9hindi.com/national/feed'"
)
conn.commit()
print("Cleaned broken sources")
conn.close()
