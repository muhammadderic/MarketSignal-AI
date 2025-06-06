from datetime import datetime, timezone
from sqlalchemy import DateTime, String, Text, func, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.modules.news.news_constants import ArticleLocale


def utc_now() -> datetime:
    """Returns the current timezone-aware UTC datetime."""
    return datetime.now(timezone.utc)

class NewsArticleData(Base):
    """Stores raw news article metadata harvested from RSS feeds."""
    
    __tablename__ = "news_article_data"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    
    title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    source: Mapped[str] = mapped_column(String(100), nullable=False)
    published_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        nullable=False, 
        index=True
    )
    link: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    locale: Mapped[ArticleLocale] = mapped_column(
        String(10), 
        default=ArticleLocale.UNASSIGNED, 
        nullable=False, 
        index=True
    )

    # LLM Financial Relevance Scoring
    relevance_score: Mapped[int | None] = mapped_column(
        nullable=True, default=None, index=True
    )
    relevance_reason: Mapped[str | None] = mapped_column(
        Text, nullable=True, default=None
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint(
            "title",
            "source",
            "published_at",
            "locale",
            name="uq_news_article_identity",
        ),
    )
    
    def __repr__(self) -> str:
        return f"<NewsArticleData(id={self.id}, source='{self.source}', published_at='{self.published_at}')>"
