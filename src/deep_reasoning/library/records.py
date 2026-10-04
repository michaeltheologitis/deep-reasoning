"""What the Library returns and raises (§4.4): pydantic models, and errors that carry
their HTTP status and JSON payload."""

from collections.abc import Sequence
from datetime import datetime
from pathlib import Path
from typing import Any, ClassVar, Literal

import yaml
from pydantic import BaseModel, ConfigDict, computed_field

Kind = Literal["profile", "namespace", "decomposition", "tool"]


class Saved(BaseModel):
    model_config = ConfigDict(frozen=True)

    version: int
    rev: int  # the revision that wrote this version
    saved_at: datetime


class ProfileRecord(Saved):
    yaml: str
    decompositions: list[str]  # top level, in order
    default_namespace: str  # entry_namespace, else "root"

    @computed_field
    @property
    def data(self) -> dict[str, Any]:
        return yaml.safe_load(self.yaml)


class NamespaceRecord(Saved):
    name: str
    yaml: str
    decompositions: list[str]  # attached, in prompt order

    @computed_field
    @property
    def data(self) -> dict[str, Any]:
        return yaml.safe_load(self.yaml)


class DecompositionRecord(Saved):
    name: str
    slug: str
    yaml: str
    use_when: str | None
    hint: str | None
    namespaces: list[str]  # derived: live namespaces whose list names it, Library order
    top_level: bool  # derived: the profile's list names it

    @computed_field
    @property
    def data(self) -> dict[str, Any]:
        return yaml.safe_load(self.yaml)


class ToolRecord(Saved):
    name: str
    yaml: str
    source: str | None
    granted_in: list[str]  # derived: live namespaces whose tools list it

    @computed_field
    @property
    def data(self) -> dict[str, Any]:
        return yaml.safe_load(self.yaml)


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


class LibraryState(BaseModel):
    model_config = ConfigDict(frozen=True)

    path: Path
    rev: int
    profile: ProfileRecord
    namespaces: dict[str, NamespaceRecord]  # root first, then creation order
    decompositions: dict[str, DecompositionRecord]  # keyed by name, in slug order
    tools: dict[str, ToolRecord]  # creation order


class Entry(BaseModel):
    kind: Kind
    name: str


class Change(Entry):
    version: int  # the version this save wrote
    created: bool  # the entity was not live before


class ImportReport(BaseModel):
    source: Path  # the main YAML read
    rev: int | None  # None: nothing changed
    changed: list[Change]
    unchanged: list[Entry]


class DecompositionMeta(BaseModel):
    use_when: str | None = None
    hint: str | None = None


class Manifest(BaseModel):
    """library.yaml in every materialized directory; dr never reads it."""

    v: Literal[1] = 1
    library: str  # the library file's absolute path
    rev: int
    namespace: str  # the entry namespace written into main.yaml
    deep_reasoner: str  # the build that validated what was written
    profile: int
    namespaces: dict[str, int]
    decompositions: dict[str, int]
    tools: dict[str, int]
    metadata: dict[str, DecompositionMeta]  # by name; import reads it back


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


class LibraryNotFound(LibraryError):
    code = "not_found"
    status = 404


class LibraryImportError(LibraryError):
    code = "import_failed"
    status = 422
