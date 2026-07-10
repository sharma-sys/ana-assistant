import sqlite3
conn = sqlite3.connect('ana.db')
try:
    sources = conn.execute("SELECT COUNT(*) FROM news_sources").fetchone()[0]
    print(f"Sources: {sources}")
except Exception as e:
    print(f"Error checking sources: {e}")

try:
    articles = conn.execute("SELECT COUNT(*) FROM news_articles").fetchone()[0]
    print(f"Articles: {articles}")
except Exception as e:
    print(f"Error checking articles: {e}")
