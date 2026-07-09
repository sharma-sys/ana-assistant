import sqlite3
import sys


def main():
    try:
        conn = sqlite3.connect("ana.db")
        c = conn.cursor()
        c.execute("ALTER TABLE news_articles ADD COLUMN language VARCHAR DEFAULT 'hi'")
        conn.commit()
        print("Column 'language' added successfully.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("Column 'language' already exists.")
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
