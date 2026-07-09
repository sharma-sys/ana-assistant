import sqlite3

conn = sqlite3.connect("ana.db")
c = conn.cursor()
c.execute("UPDATE news_sources SET is_active=0 WHERE name='Zee News - Hindi'")
conn.commit()
print("Zee News Disabled:", c.rowcount)
conn.close()
