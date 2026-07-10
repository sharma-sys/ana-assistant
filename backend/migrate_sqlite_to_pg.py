import sqlite3
from database.session import get_db
from database.models import NewsSource

def migrate():
    # Read from sqlite
    conn = sqlite3.connect('ana.db')
    c = conn.cursor()
    c.execute("SELECT name, type, url, state, district, department, category, is_active FROM news_sources")
    rows = c.fetchall()
    conn.close()

    # Insert to postgres
    db = next(get_db())
    inserted = 0
    for row in rows:
        exists = db.query(NewsSource).filter(NewsSource.url == row[2]).first()
        if not exists:
            source = NewsSource(
                name=row[0],
                type=row[1],
                url=row[2],
                state=row[3],
                district=row[4],
                department=row[5],
                category=row[6],
                is_active=bool(row[7])
            )
            db.add(source)
            inserted += 1

    db.commit()
    print(f"Migrated {inserted} sources from SQLite to PostgreSQL.")

if __name__ == "__main__":
    migrate()
