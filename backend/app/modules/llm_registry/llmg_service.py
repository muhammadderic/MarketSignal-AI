from sqlalchemy.exc import SQLAlchemyError

from app.integrations.adapters import GroqAdapter
from app.shared.schemas import ModelInfo, ModelsResponse
from app.modules.llm_registry.llmg_repo import LLMRegistryRepo


class LLMRegistryService:
    """Service for managing LLM model metadata."""

    def __init__(
        self,
        repo: LLMRegistryRepo,
        adapter: GroqAdapter,
    ):
        self.repo = repo
        self.adapter = adapter

    async def fetch_list_models(self) -> ModelsResponse:
        """
        Return the list of LLM models, sourcing from the database when
        populated and falling back to the external provider otherwise.

        Flow:
            1. Read from local DB. If populated, return immediately.
            2. Otherwise, fetch from the Groq adapter (list[ExternalModelInfo]).
            3. Persist the fetched models.
            4. Re-read from the DB to return a fresh, canonical list,
               with the count computed only in `_to_response`.
        """
        # 1. Try the database first.
        rows = self.repo.get_all_models()
        if rows:
            return self._to_response(rows)

        # 2. Fall back to the external provider.
        external_models = await self.adapter.list_models()

        # 3. Persist (adapter already emits UTC-aware created_date).
        records = [
            {
                "model_id": info.model_id,
                "object_type": info.object_type,
                "owned_by": info.owned_by,
                "active": info.active,
                "context_window": info.context_window,
                "created_date": info.created_date,
            }
            for info in external_models
        ]

        try:
            self.repo.create_all_models(records)
            self.repo.db.commit()
        except SQLAlchemyError:
            self.repo.db.rollback()
            raise

        # 4. Re-read from DB to return canonical state.
        rows = self.repo.get_all_models()
        return self._to_response(rows)

    @staticmethod
    def _to_response(rows) -> ModelsResponse:
        """Map ORM rows into the response schema."""
        models = [
            ModelInfo(
                id=row.id,
                model_id=row.model_id,
                object_type=row.object_type,
                owned_by=row.owned_by,
                active=row.active,
                context_window=row.context_window,
                created_date=row.created_date,
            )
            for row in rows
        ]
        return ModelsResponse(models=models, count=len(models))
