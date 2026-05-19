"""Tests for security helpers used to validate paths and collection names."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.core.security import resolve_path_under_base, validate_collection_name


def test_validate_collection_name_accepts_safe_names() -> None:
    assert validate_collection_name("default") == "default"
    assert validate_collection_name("rag_docs-01") == "rag_docs-01"


@pytest.mark.parametrize("collection", ["../../etc", "a/b", r"..\\tmp", "white space", ""])
def test_validate_collection_name_rejects_unsafe_values(collection: str) -> None:
    with pytest.raises(ValueError):
        validate_collection_name(collection)


def test_resolve_path_under_base_allows_nested_file(tmp_path: Path) -> None:
    base = tmp_path / "images"
    nested = base / "collection" / "img.png"
    nested.parent.mkdir(parents=True)
    nested.write_bytes(b"data")

    resolved = resolve_path_under_base(nested, base)

    assert resolved == nested.resolve()


def test_resolve_path_under_base_rejects_escape(tmp_path: Path) -> None:
    base = tmp_path / "images"
    base.mkdir()
    outside = tmp_path / "secret.txt"
    outside.write_text("secret")

    with pytest.raises(ValueError, match="escapes allowed directory"):
        resolve_path_under_base(outside, base)
