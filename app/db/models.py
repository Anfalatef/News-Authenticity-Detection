"""
Database models definition.

Tables:
- sources
- articles
- chunks
- embeddings
"""

from datetime import datetime

from sqlalchemy import (
    Column,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.db.connection import Base


def utc_now_iso() -> str:
    """Return current UTC time as ISO string."""
    return datetime.utcnow().isoformat(timespec="seconds")


class Source(Base):
    """
    News publisher / source.

    Example:
    - name: 'Roya News'
    - domain: 'royanews.tv'
    """

    __tablename__ = "sources"

    source_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    domain = Column(String(255), nullable=False, unique=True)
    country = Column(String(64), nullable=True)
    trust_level = Column(Integer, nullable=False, default=0)
    created_at = Column(String(32), nullable=False, default=utc_now_iso)

    articles = relationship(
        "Article",
        back_populates="source",
        cascade="all, delete-orphan",
    )


class Article(Base):
    """
    Scraped news article.
    """

    __tablename__ = "articles"

    article_id = Column(Integer, primary_key=True, autoincrement=True)

    source_id = Column(
        Integer,
        ForeignKey("sources.source_id"),
        nullable=False,
    )

    url = Column(Text, nullable=False, unique=True)
    title = Column(Text, nullable=True)

    published_at = Column(String(32), nullable=True)
    scraped_at = Column(String(32), nullable=False, default=utc_now_iso)

    language = Column(String(8), nullable=True)  # 'ar', 'en', etc.
    clean_text = Column(Text, nullable=False)    # Full cleaned article text
    summary = Column(Text, nullable=True)        # Optional LLM-generated summary
    content_hash = Column(String(64), nullable=True)

    source = relationship("Source", back_populates="articles")

    chunks = relationship(
        "Chunk",
        back_populates="article",
        cascade="all, delete-orphan",
    )


Index("idx_articles_source", Article.source_id)
Index("idx_articles_language", Article.language)


class Chunk(Base):
    """
    Evidence-ready segment of an article.
    Used for retrieval (RAG).
    """

    __tablename__ = "chunks"

    chunk_id = Column(Integer, primary_key=True, autoincrement=True)

    article_id = Column(
        Integer,
        ForeignKey("articles.article_id"),
        nullable=False,
    )

    chunk_index = Column(Integer, nullable=False)  # Order within the article
    chunk_text = Column(Text, nullable=False)
    created_at = Column(String(32), nullable=False, default=utc_now_iso)

    article = relationship("Article", back_populates="chunks")

    embedding = relationship(
        "Embedding",
        back_populates="chunk",
        uselist=False,
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint(
            "article_id",
            "chunk_index",
            name="uq_chunks_article_index",
        ),
    )


Index("idx_chunks_article", Chunk.article_id)


class Embedding(Base):
    """
    Mapping between a text chunk and its FAISS vector.
    """

    __tablename__ = "embeddings"

    embedding_id = Column(Integer, primary_key=True, autoincrement=True)

    chunk_id = Column(
        Integer,
        ForeignKey("chunks.chunk_id"),
        nullable=False,
        unique=True,
    )

    faiss_id = Column(Integer, nullable=False, unique=True)

    model_name = Column(Text, nullable=False)
    dim = Column(Integer, nullable=False)
    created_at = Column(String(32), nullable=False, default=utc_now_iso)

    chunk = relationship("Chunk", back_populates="embedding")


Index("idx_embeddings_faiss", Embedding.faiss_id)


from sqlalchemy import Column, Integer, String, DateTime, Text
from datetime import datetime

class AnalysisLog(Base):
    __tablename__ = "analysis_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(String, default=lambda: datetime.utcnow().isoformat(timespec="seconds"))
    input_text = Column(Text, nullable=False)
    response_json = Column(Text, nullable=False)

    status = Column(String, default="ok")  # ok / error
    latency_ms = Column(Integer, default=0)

    used_cse = Column(Integer, default=0)  # 0/1
    retrieved_count = Column(Integer, default=0)

    error_message = Column(Text, nullable=True)
