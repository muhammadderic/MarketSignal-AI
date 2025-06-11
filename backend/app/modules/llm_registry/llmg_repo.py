from typing import Sequence
from sqlalchemy import select, insert
from sqlalchemy.orm import Session

from app.modules.llm_registry.models import LLMModelData


class LLMRegistryRepo:
    """Repository for LLM model metadata."""

    def __init__(self, db: Session):
        self.db = db

    def get_all_models(self) -> Sequence[LLMModelData]:
        """
        Fetch all stored LLM model records, ordered by model_id.

        Returns:
            Sequence of LLMModelData ORM instances.
        """
        stmt = select(LLMModelData).order_by(LLMModelData.model_id)
        return self.db.scalars(stmt).all()

    def create_all_models(self, records: list[dict]) -> None:
        """
        Bulk-insert LLM model records.

        Args:
            records: List of dicts matching LLMModelData columns.

        Returns:
            None.
        """
        if not records:
            return

        stmt = insert(LLMModelData).values(records)
        self.db.execute(stmt)
