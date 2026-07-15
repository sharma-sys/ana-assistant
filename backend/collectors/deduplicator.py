import hashlib
import spacy
import logging
from sqlalchemy.orm import Session
from database.models import NewsArticle

logger = logging.getLogger(__name__)

# Load spacy model globally to avoid loading overhead per check
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    logger.warning("Spacy model not found. Similarity checks will be disabled.")
    nlp = None

class Deduplicator:
    def __init__(self, db: Session):
        self.db = db
        # Cache URLs and hashes we've already checked this session
        self.seen_urls = set()
        self.seen_titles = set()
        self.seen_hashes = set()

    def _generate_hash(self, content: str) -> str:
        """Level 3: MD5 hash generation"""
        if not content:
            return ""
        return hashlib.md5(content.encode('utf-8')).hexdigest()

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Level 4: NLP similarity calculation using Spacy"""
        if not nlp or not text1 or not text2:
            return 0.0
        doc1 = nlp(text1[:1000]) # Limit to first 1000 chars for performance
        doc2 = nlp(text2[:1000])
        return doc1.similarity(doc2)

    def is_duplicate(self, title: str, link: str, content: str = "") -> bool:
        """
        Smart Deduplication using multiple levels:
        Level 1: URL
        Level 2: Title
        Level 3: Content Hash
        Level 4: Similarity
        """
        # --- Level 1: URL Match ---
        if link in self.seen_urls:
            return True
        exists_url = self.db.query(NewsArticle).filter(NewsArticle.source_url == link).first()
        if exists_url:
            self.seen_urls.add(link)
            return True
            
        # --- Level 2: Title Match ---
        clean_title = title.strip().lower() if title else ""
        if clean_title:
            if clean_title in self.seen_titles:
                self.seen_urls.add(link)
                return True
            exists_title = self.db.query(NewsArticle).filter(NewsArticle.title.ilike(f"%{clean_title}%")).first()
            if exists_title:
                self.seen_titles.add(clean_title)
                self.seen_urls.add(link)
                return True

        # --- Level 3: Content Hash Match ---
        content_hash = self._generate_hash(content)
        if content_hash:
            if content_hash in self.seen_hashes:
                self.seen_urls.add(link)
                return True
            # Assuming we can't easily query DB by hash if the column doesn't exist.
            # But wait, there's no `hash` column in NewsArticle according to models.py.
            # "Keep existing schema. No breaking migrations."
            # So I will only rely on in-session hash matching to prevent batch duplicates.
            self.seen_hashes.add(content_hash)

        # --- Level 4: Similarity Check against recent articles ---
        if nlp and content:
            # We fetch a few very recent articles to check similarity and avoid N+1 issues
            recent_articles = self.db.query(NewsArticle).order_by(NewsArticle.published_at.desc()).limit(10).all()
            for article in recent_articles:
                # We can't compare full DB content since NewsArticle doesn't store full content directly?
                # Oh wait, models.py doesn't have a full `content` column in NewsArticle, only in AIResult.
                # However, it might be stored somewhere else or just title. Let's compare titles.
                if article.title:
                    sim = self._calculate_similarity(clean_title, article.title.lower())
                    if sim > 0.85:
                        self.seen_urls.add(link)
                        return True

        # Cache valid lookups
        self.seen_urls.add(link)
        if clean_title:
            self.seen_titles.add(clean_title)
            
        return False
