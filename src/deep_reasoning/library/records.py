"""What the Library returns and raises (§4.4): pydantic models, and errors that carry
their HTTP status and JSON payload."""

from collections.abc import Sequence
from datetime import datetime
from typing import Any, ClassVar, Literal

from pydantic import BaseModel, ConfigDict

Kind = Literal["profile", "namespace", "decomposition", "tool"]


class Saved(BaseModel):
    model_config = ConfigDict(frozen=True)

    version: int
    rev: int  # the revision that wrote this version
    saved_at: datetime


class HistoryEntry(Saved):
    """One stored version, with its revision's time and action; a tombstone is deleted
    and has no yaml."""

    kind: Kind
    name: str
    action: str  # the revision's action
    deleted: bool
    yaml: str | None
    decompositions: list[str] | None  # profile, namespace
    slug: str | None
    use_when: str | None
    hint: str | None
    source: str | None
    deep_reasoner: str


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
