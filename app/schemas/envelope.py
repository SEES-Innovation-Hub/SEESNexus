from typing import Any, Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class Envelope(BaseModel, Generic[T]):
    """{status, message, data} envelope required by Tech Doc §5."""

    status: str
    message: str
    data: T | None = None


def success(data: Any = None, message: str = "OK") -> dict:
    return {"status": "success", "message": message, "data": data}


def error(message: str = "Error", data: Any = None) -> dict:
    return {"status": "error", "message": message, "data": data}
