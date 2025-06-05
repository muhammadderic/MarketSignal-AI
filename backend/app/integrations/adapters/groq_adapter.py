from app.integrations.clients import GroqClient
from app.shared.schemas import ModelsResponse, ModelInfo


class GroqAdapter:
    def __init__(self, client: GroqClient):
        self.client = client

    async def list_models(self) -> ModelsResponse:
        models_data = await self.client.list_available_models()
        
        models = []
        for model in models_data:
            model_info = ModelInfo(
                id=model.id,
                object=model.object,
                created=model.created,
                owned_by=model.owned_by,
                active=getattr(model, "active", True),
                context_window=getattr(model, "context_window", None),
            )
            models.append(model_info)
        
        return ModelsResponse(models=models, count=len(models))