"""Focused security tests for OpenAI-compatible Vision LLM path handling."""

from __future__ import annotations

import base64

import pytest

from src.libs.llm.base_vision_llm import ImageInput
from src.libs.llm.openai_vision_llm import OpenAIVisionLLM, OpenAIVisionLLMError


class MockSettings:
    """Minimal settings object for OpenAIVisionLLM tests."""

    class LLMSettings:
        provider = "openai"
        model = "gpt-4o"
        temperature = 0.0
        max_tokens = 256
        api_key = "test-key"
        api_version = None
        azure_endpoint = None
        deployment_name = None
        base_url = None

    class VisionLLMSettings:
        enabled = True
        provider = "openai"
        model = "gpt-4o"
        api_key = "test-key"
        api_version = None
        azure_endpoint = None
        deployment_name = None
        base_url = None
        max_image_size = 2048

    def __init__(self) -> None:
        self.llm = self.LLMSettings()
        self.vision_llm = self.VisionLLMSettings()


def test_get_image_base64_from_path_within_allowed_root(tmp_path) -> None:
    """Allow reading images that stay within the configured image root."""
    allowed_root = tmp_path / "images"
    allowed_root.mkdir()
    image_path = allowed_root / "safe.png"
    image_path.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 16)

    llm = OpenAIVisionLLM(MockSettings(), allowed_image_root=allowed_root)

    encoded = llm._get_image_base64(ImageInput(path=str(image_path)))

    assert base64.b64decode(encoded) == image_path.read_bytes()


def test_get_image_base64_rejects_path_outside_allowed_root(tmp_path) -> None:
    """Reject local file reads that escape the configured image root."""
    allowed_root = tmp_path / "allowed"
    allowed_root.mkdir()

    outside_root = tmp_path / "outside"
    outside_root.mkdir()
    image_path = outside_root / "secret.png"
    image_path.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x01" * 16)

    llm = OpenAIVisionLLM(MockSettings(), allowed_image_root=allowed_root)

    with pytest.raises(OpenAIVisionLLMError, match="Invalid image path"):
        llm._get_image_base64(ImageInput(path=str(image_path)))
