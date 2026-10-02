"""The Library: namespaces, decompositions, tools and one profile, as canonical YAML in
one SQLite file per user, every save an immutable version (D2).

Library and Effective are imported on first use: they import deep_reasoner, and dr-acp
builds its LibraryCatalog before it serves.
"""

import importlib
from typing import Any

from deep_reasoning.library.catalog import LibraryCatalog
from deep_reasoning.library.records import (
    DecompositionMeta,
    DecompositionRecord,
    HistoryEntry,
    ImportReport,
    LibraryConflict,
    LibraryError,
    LibraryImportError,
    LibraryNotFound,
    LibraryRefused,
    LibraryState,
    LibraryValidationError,
    Manifest,
    NamespaceRecord,
    Problem,
    ProfileRecord,
    ToolRecord,
    ValidationResult,
)

_LAZY = {
    "LIBRARY_FILE": "library",
    "Library": "library",
    "library_path": "library",
    "Effective": "effective",
}

__all__ = [
    "LIBRARY_FILE",
    "DecompositionMeta",
    "DecompositionRecord",
    "Effective",
    "HistoryEntry",
    "ImportReport",
    "Library",
    "LibraryCatalog",
    "LibraryConflict",
    "LibraryError",
    "LibraryImportError",
    "LibraryNotFound",
    "LibraryRefused",
    "LibraryState",
    "LibraryValidationError",
    "Manifest",
    "NamespaceRecord",
    "Problem",
    "ProfileRecord",
    "ToolRecord",
    "ValidationResult",
    "library_path",
]


def __getattr__(name: str) -> Any:
    if name not in _LAZY:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    return getattr(importlib.import_module(f"{__name__}.{_LAZY[name]}"), name)
