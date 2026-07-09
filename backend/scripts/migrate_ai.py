import sqlite3
import os

def migrate():
    db_path = os.path.join(os.path.dirname(__file__), 'ana.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    columns_to_add = [
        "summary TEXT",
        "category TEXT",
        "reading_time TEXT",
        "translation TEXT",
        "related_articles TEXT"
    ]
    
    for col in columns_to_add:
        try:
            cursor.execute(f"ALTER TABLE ai_results ADD COLUMN {col}")
            print(f"Added column {col}")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print(f"Column {col.split()[0]} already exists.")
            else:
                print(f"Error adding {col}: {e}")
                
    conn.commit()
    conn.close()

if __name__ == "__main__":
    migrate()
