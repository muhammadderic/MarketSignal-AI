from typing import Any
from pydantic import BaseModel


class ErrorResponse(BaseModel):
    status: str = "error"
    code: str
    message: str
    details: dict[str, Any] | list[Any] | None = None