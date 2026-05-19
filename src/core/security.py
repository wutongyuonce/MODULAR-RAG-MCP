"""Security helpers for validating untrusted file paths and collection names."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Union


COLLECTION_NAME_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")


def validate_collection_name(collection: str) -> str:
    """Validate a collection name used in filesystem-backed storage paths."""
    if not isinstance(collection, str):
        raise ValueError(f"Collection name must be a string, got {type(collection).__name__}")

    normalized = collection.strip()
    if not normalized:
        raise ValueError("Collection name cannot be empty")

    if not COLLECTION_NAME_PATTERN.fullmatch(normalized):
        raise ValueError(
            "Invalid collection name. Only letters, numbers, underscores, and hyphens are allowed."
        )

    return normalized


def resolve_path_under_base(
    candidate_path: Union[str, Path],
    base_dir: Union[str, Path],
) -> Path:
    """Resolve a path and ensure it stays within a trusted base directory."""
    base = Path(base_dir).resolve()
    candidate = Path(candidate_path)

    if not candidate.is_absolute():
        candidate = base / candidate

    resolved = candidate.resolve()

    try:
        resolved.relative_to(base)
    except ValueError as exc:
        raise ValueError(f"Path escapes allowed directory: {candidate_path}") from exc

    return resolved
