"""What the Library returns and raises (§4.4): pydantic models, and errors that carry
their HTTP status and JSON payload."""

from collections.abc import Sequence
from typing import Any, ClassVar

from pydantic import BaseModel


class FieldError(BaseModel):
    loc: str  # "messages.0.role"; "name" for the Library's own rules; "" for the whole
    msg: str


class LibraryError(Exception):
    code: ClassVar[str] = "error"
    status: ClassVar[int] = 400

    def __init__(self, message: str) -> None:
        super().__init__(message)

    def payload(self) -> dict[str, Any]:
        """{"error": code, "message": str(self), **extra}."""
        return {"error": self.code, "message": str(self)}


class LibraryValidationError(LibraryError):
    code = "invalid"
    status = 422

    def __init__(self, message: str, errors: Sequence[FieldError]) -> None:
        super().__init__(message)
        self.errors = list(errors)

    def payload(self) -> dict[str, Any]:
        return {**super().payload(), "errors": [e.model_dump() for e in self.errors]}
