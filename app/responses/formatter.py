from typing import Any, Optional
from pydantic import BaseModel


class APIResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Any] = None
    meta: Optional[dict] = None


def format_response(
    data: Any = None,
    message: str = "Success",
    success: bool = True,
    meta: Optional[dict] = None,
):
    return APIResponse(success=success, message=message, data=data, meta=meta)
