import sqlite3

conn = sqlite3.connect("ana.db")
c = conn.cursor()
c.execute(
    "UPDATE news_sources SET url='https://tv9hindi.com/feed' WHERE name='TV9 Bharatvarsh - Hindi'"
)
conn.commit()
print("TV9 URL Updated:", c.rowcount)
conn.close()
