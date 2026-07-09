import sqlite3
import sys


def main():
    try:
        conn = sqlite3.connect("ana.db")
        c = conn.cursor()

        # Add to news_sources
        try:
            c.execute("ALTER TABLE news_sources ADD COLUMN department VARCHAR")
            print("Column 'department' added successfully to news_sources.")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                print("Column 'department' already exists in news_sources.")
            else:
                raise e

        # Add to news_articles
        try:
            c.execute("ALTER TABLE news_articles ADD COLUMN department VARCHAR")
            print("Column 'department' added successfully to news_articles.")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                print("Column 'department' already exists in news_articles.")
            else:
                raise e

        conn.commit()
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
    finally:
        if "conn" in locals():
            conn.close()


if __name__ == "__main__":
    main()
