import sqlite3


def run_migration():
    conn = sqlite3.connect("ana.db")
    cursor = conn.cursor()

    try:
        cursor.execute("ALTER TABLE news_sources ADD COLUMN category TEXT;")
        print("Added category column to news_sources.")
    except sqlite3.OperationalError as e:
        print(f"Error (news_sources): {e}")

    try:
        cursor.execute("ALTER TABLE news_articles ADD COLUMN category TEXT;")
        print("Added category column to news_articles.")
    except sqlite3.OperationalError as e:
        print(f"Error (news_articles): {e}")

    # Set default category to 'National' where state is 'National', otherwise 'General'
    cursor.execute(
        "UPDATE news_sources SET category = 'National' WHERE state = 'National';"
    )
    cursor.execute(
        "UPDATE news_articles SET category = 'National' WHERE state = 'National';"
    )

    conn.commit()
    conn.close()
    print("Migration complete.")


if __name__ == "__main__":
    run_migration()
