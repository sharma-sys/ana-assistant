import sqlite3
import os

def update_db():
    db_path = os.path.join(os.path.dirname(__file__), '..', 'ana.db')
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    c.execute("SELECT id, name, type, category FROM news_sources")
    rows = c.fetchall()
    ids_to_delete = []
    for row in rows:
        id, name, type, category = row
        name_l = name.lower()
        if type == 'rss_hindi': continue
        if 'hindi' in name_l: continue
        if 'bhaskar' in name_l or 'jagran' in name_l or 'lallantop' in name_l: continue
        if type == 'google_news' and any(x in name for x in ['भारत', 'भोपाल', 'मध्यप्रदेश', 'इंदौर', 'उत्तर प्रदेश', 'बिहार', 'राजस्थान', 'राजनीति', 'खेल', 'शिक्षा', 'अपराध']): continue
        if type in ['rss_gov', 'rss_police', 'rss_pib']: continue
        
        print(f"Deleting English source: {name} (Type: {type})")
        ids_to_delete.append(id)
        
    for id in ids_to_delete:
        c.execute("DELETE FROM news_sources WHERE id = ?", (id,))
        c.execute("DELETE FROM news_articles WHERE source_id = ?", (id,))
        
    new_sources = [
        ("Zee News Hindi", "rss_hindi", "https://zeenews.india.com/hindi/india/rss", "All", 1, None, None, "National"),
        ("News18 Hindi", "rss_hindi", "https://hindi.news18.com/rss/khabar/nation/nation.xml", "All", 1, None, None, "National"),
        ("Haribhoomi", "rss_hindi", "https://www.haribhoomi.com/rss/india", "All", 1, None, None, "National"),
        ("Patrika", "rss_hindi", "https://www.patrika.com/rss.xml", "All", 1, None, None, "National"),
        ("Amar Ujala", "rss_hindi", "https://www.amarujala.com/rss/india-news.xml", "All", 1, None, None, "National"),
        ("Hindustan Times", "rss", "https://www.hindustantimes.com/feeds/rss/india-news/rssfeed.xml", "All", 1, None, None, "National"),
        ("Indian Express", "rss", "https://indianexpress.com/section/india/feed/", "All", 1, None, None, "National"),
        ("India Today", "rss", "https://www.indiatoday.in/rss/1206584", "All", 1, None, None, "National"),
        ("DD News", "rss", "https://ddnews.gov.in/rss", "All", 1, None, None, "National"),
        ("ANI", "rss", "https://www.aninews.in/rss/feed/category/national/", "All", 1, None, None, "National")
    ]
    
    for src in new_sources:
        c.execute("SELECT id FROM news_sources WHERE name = ?", (src[0],))
        if not c.fetchone():
            print(f"Adding new source: {src[0]}")
            c.execute("INSERT OR IGNORE INTO news_sources (name, type, url, state, is_active, district, department, category) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", src)

    conn.commit()
    print("Database updated!")

if __name__ == '__main__':
    update_db()
