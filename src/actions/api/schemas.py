from __future__ import annotations

from typing import Any, Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


# --- Schema of Global Api Response ---
class ApiResponseSchema(BaseModel, Generic[T]):
    """Pydantic schema of global api response"""

    message: str
    status_code: int
    data: T | None = None
    meta: dict[str, Any] | None = None
