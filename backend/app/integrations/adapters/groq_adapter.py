from app.integrations.clients import GroqClient
from app.modules.llm_registry.llmg_schemas import ExternalModelInfo
from app.modules.llm_registry.llmg_utils import epoch_to_utc_datetime


class GroqAdapter:
    def __init__(self, client: GroqClient):
        self.client = client

    async def list_models(self) -> list[ExternalModelInfo]:
        """
        Fetch available LLM models from Groq and normalize them into
        persistence-agnostic `ExternalModelInfo` objects.

        The provider's Unix `created` timestamp is converted to a
        UTC-aware datetime via `epoch_to_utc_datetime`. The returned
        list has no `id` (DB assigns it) and no count wrapper (the
        service computes the total).

        Returns:
            A list of ExternalModelInfo, one per provider model.
        """
        models_data = await self.client.list_available_models()

        return [
            ExternalModelInfo(
                model_id=model.id,
                object_type=model.object,
                owned_by=model.owned_by,
                active=getattr(model, "active", True),
                context_window=getattr(model, "context_window", 0),
                created_date=epoch_to_utc_datetime(model.created),
            )
            for model in models_data
        ]
