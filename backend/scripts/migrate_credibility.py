import sqlite3
import os

def migrate():
    db_path = os.path.join(os.path.dirname(__file__), 'ana.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        cursor.execute("ALTER TABLE news_articles ADD COLUMN credibility_score INTEGER")
        print("Added column credibility_score to news_articles")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print("Column credibility_score already exists.")
        else:
            print(f"Error: {e}")
            
    conn.commit()
    conn.close()

if __name__ == "__main__":
    migrate()
