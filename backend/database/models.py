from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
import datetime
from .session import Base


class NewsSource(Base):
    __tablename__ = "news_sources"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    type = Column(String)  # 'rss', 'api', etc.
    url = Column(String, unique=True)
    state = Column(String, index=True)
    district = Column(String, index=True, nullable=True)
    department = Column(String, index=True, nullable=True)
    category = Column(String, index=True, nullable=True)
    is_active = Column(Boolean, default=True)

    articles = relationship("NewsArticle", back_populates="source_rel")


class NewsArticle(Base):
    __tablename__ = "news_articles"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    source_url = Column(String, unique=True, index=True)
    source_id = Column(Integer, ForeignKey("news_sources.id"), index=True)
    state = Column(String, index=True)
    district = Column(String, index=True)
    category = Column(String, index=True, nullable=True)
    published_at = Column(DateTime, index=True)
    status = Column(String, default="pending")  # 'pending', 'processed', 'published'
    image_url = Column(String, nullable=True)
    language = Column(String, default="hi")
    department = Column(String, index=True, nullable=True)
    references = Column(Text, nullable=True)
    credibility_score = Column(Integer, nullable=True)

    source_rel = relationship("NewsSource", back_populates="articles")
    ai_result = relationship("AIResult", back_populates="article", uselist=False)


class AIResult(Base):
    __tablename__ = "ai_results"

    id = Column(Integer, primary_key=True, index=True)
    article_id = Column(Integer, ForeignKey("news_articles.id"), unique=True)
    content = Column(Text)
    seo_title = Column(String)
    meta_description = Column(String)
    keywords = Column(String)
    slug = Column(String)
    summary = Column(Text, nullable=True)
    category = Column(String, nullable=True)
    reading_time = Column(String, nullable=True)
    translation = Column(Text, nullable=True)
    related_articles = Column(Text, nullable=True)

    article = relationship("NewsArticle", back_populates="ai_result")


class Setting(Base):
    __tablename__ = "settings"

    key = Column(String, primary_key=True, index=True)
    value = Column(String)


class Log(Base):
    __tablename__ = "logs"

    id = Column(Integer, primary_key=True, index=True)
    level = Column(String)  # 'info', 'error', 'warning'
    message = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
