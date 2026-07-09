import sqlite3


def migrate():
    try:
        conn = sqlite3.connect("ana.db")
        cursor = conn.cursor()
        cursor.execute('ALTER TABLE news_articles ADD COLUMN "references" TEXT')
        conn.commit()
        print("Migration successful")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()


if __name__ == "__main__":
    migrate()
