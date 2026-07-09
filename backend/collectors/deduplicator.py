from sqlalchemy.orm import Session
from database.models import NewsArticle

class Deduplicator:
    def __init__(self, db: Session):
        self.db = db
        # Cache URLs we've already checked this session to avoid repeated DB queries
        self.seen_urls = set()
        
    def is_duplicate(self, title: str, link: str) -> bool:
        if link in self.seen_urls:
            return True
            
        # Check if the article already exists in the database
        exists = self.db.query(NewsArticle).filter(NewsArticle.source_url == link).first()
        if exists:
            self.seen_urls.add(link)
            return True
            
        # Add to seen_urls so we don't process it again in the same run
        self.seen_urls.add(link)
        return False
