"""The Library: namespaces, decompositions, tools and one profile, as canonical YAML in
one SQLite file per user, every save an immutable version.

Library and Effective are imported on first use, because they import deep_reasoner;
importing this package, LibraryCatalog or library_path does not.
"""

import importlib
from typing import Any

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
    ProfileRecord,
    ToolRecord,
    ValidationResult,
)

_LAZY = {"Library": "library", "Effective": "effective"}

__all__ = [
    "DecompositionMeta",
    "DecompositionRecord",
    "HistoryEntry",
    "ImportReport",
    "Library",
    "LibraryConflict",
    "LibraryError",
    "LibraryImportError",
    "LibraryNotFound",
    "LibraryRefused",
    "LibraryState",
    "LibraryValidationError",
    "Manifest",
    "NamespaceRecord",
    "ProfileRecord",
    "ToolRecord",
    "ValidationResult",
]


def __getattr__(name: str) -> Any:
    if name not in _LAZY:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    return getattr(importlib.import_module(f"{__name__}.{_LAZY[name]}"), name)
