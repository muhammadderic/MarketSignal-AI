from datetime import datetime

from sqlalchemy import DateTime, String, func, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.shared.utils import utc_now


class LLMModelData(Base):
    """Stores metadata about LLM models available from external providers."""

    __tablename__ = "llm_model_data"

    id: Mapped[int] = mapped_column(primary_key=True)

    model_id: Mapped[str] = mapped_column(String(100), nullable=False)
    object_type: Mapped[str] = mapped_column(String(20), nullable=False)
    owned_by: Mapped[str] = mapped_column(String(100), nullable=False)
    active: Mapped[bool] = mapped_column(nullable=False, default=True)
    context_window: Mapped[int] = mapped_column(nullable=False)

    created_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
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
            "model_id",
            "owned_by",
            name="uq_llm_model_identity",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<LLMModelData(id={self.id}, model_id='{self.model_id}', "
            f"owned_by='{self.owned_by}')>"
        )
        