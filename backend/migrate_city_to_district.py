import sqlite3
import sys
import os

def main():
    db_path = os.path.join(os.path.dirname(__file__), "ana.db")
    try:
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        
        # In SQLite, we can just RENAME COLUMN
        c.execute("ALTER TABLE news_articles RENAME COLUMN city TO district")
        conn.commit()
        print("Successfully renamed 'city' to 'district' in news_articles.")
    except sqlite3.OperationalError as e:
        if "no such column: city" in str(e):
            print("Column 'city' does not exist or has already been renamed.")
        else:
            print(f"Operational error: {e}")
            sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
    finally:
        if "conn" in locals():
            conn.close()

if __name__ == "__main__":
    main()
