"""Dashboard configuration reading service.

Wraps :class:`Settings` to provide formatted component information
for the Overview page.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from src.core.settings import Settings, load_settings


@dataclass
class ComponentField:
    """A labeled summary field shown on a component card."""

    label: str
    value: str


@dataclass
class ComponentInfo:
    """Summary of a single configured component."""

    name: str
    summary: List[ComponentField]
    extra: Dict[str, Any]
    status: Optional[str] = None


class ConfigService:
    """Read-only service that exposes application configuration.

    Args:
        settings_path: Path to ``settings.yaml``.
    """

    def __init__(self, settings_path: Optional[str] = None) -> None:
        self._settings_path = settings_path
        self._settings: Optional[Settings] = None

    # ── lazy load ────────────────────────────────────────────────────

    def _load(self) -> Settings:
        if self._settings is None:
            self._settings = load_settings(self._settings_path)
        return self._settings

    def reload(self) -> None:
        """Force reload of settings from disk."""
        self._settings = None

    @property
    def settings(self) -> Settings:
        return self._load()

    # ── component cards ──────────────────────────────────────────────

    def get_component_cards(self) -> List[ComponentInfo]:
        """Return a list of component summaries for the Overview page."""
        s = self._load()
        cards: List[ComponentInfo] = []

        # LLM
        cards.append(ComponentInfo(
            name="LLM",
            summary=[
                ComponentField(label="Provider", value=s.llm.provider),
                ComponentField(label="Model", value=s.llm.model),
            ],
            extra={"temperature": s.llm.temperature, "max_tokens": s.llm.max_tokens},
        ))

        # Embedding
        cards.append(ComponentInfo(
            name="Embedding",
            summary=[
                ComponentField(label="Provider", value=s.embedding.provider),
                ComponentField(label="Model", value=s.embedding.model),
            ],
            extra={"dimensions": s.embedding.dimensions},
        ))

        # VectorStore
        cards.append(ComponentInfo(
            name="Vector Store",
            summary=[
                ComponentField(label="Engine", value=s.vector_store.provider),
                ComponentField(
                    label="Default Collection",
                    value=s.vector_store.collection_name,
                ),
            ],
            extra={"persist_directory": s.vector_store.persist_directory},
        ))

        # Query Orchestration
        orchestration = s.retrieval.query_orchestration
        orchestration_enabled = orchestration.enabled
        cards.append(ComponentInfo(
            name="Query Orchestration",
            summary=[
                ComponentField(
                    label="Planner",
                    value=orchestration.planner_provider if orchestration_enabled else "-",
                ),
                ComponentField(
                    label="Configured Mode",
                    value=orchestration.mode if orchestration_enabled else "off",
                ),
            ],
            extra={
                "enabled": orchestration_enabled,
                "max_sub_queries": orchestration.max_sub_queries,
                "parallel_sub_queries": (
                    orchestration.parallel_sub_queries
                    if orchestration.mode == "decomposition"
                    else False
                ),
                "merge_fusion (decomposition)": orchestration.merge_fusion,
            },
            status="enabled" if orchestration_enabled else "disabled",
        ))

        # Retrieval
        cards.append(ComponentInfo(
            name="Retrieval",
            summary=[
                ComponentField(label="Pipeline", value="hybrid"),
                ComponentField(label="Rank Fusion", value="dense + sparse -> RRF"),
            ],
            extra={
                "dense_top_k": s.retrieval.dense_top_k,
                "sparse_top_k": s.retrieval.sparse_top_k,
                "fusion_top_k": s.retrieval.fusion_top_k,
            },
        ))

        # Rerank
        rerank_enabled = s.rerank.enabled
        cards.append(ComponentInfo(
            name="Reranker",
            summary=[
                ComponentField(
                    label="Type",
                    value=s.rerank.provider if rerank_enabled else "-",
                ),
                ComponentField(label="Top K", value=str(s.rerank.top_k)),
            ],
            extra={
                "enabled": rerank_enabled,
                "configured_model": s.rerank.model,
            },
            status="enabled" if rerank_enabled else "disabled",
        ))

        # Vision LLM
        if s.vision_llm:
            vision_enabled = s.vision_llm.enabled
            cards.append(ComponentInfo(
                name="Vision LLM",
                summary=[
                    ComponentField(label="Provider", value=s.vision_llm.provider),
                    ComponentField(label="Model", value=s.vision_llm.model),
                ],
                extra={
                    "enabled": vision_enabled,
                    "max_image_size": s.vision_llm.max_image_size,
                },
                status="enabled" if vision_enabled else "disabled",
            ))

        # Ingestion
        if s.ingestion:
            cards.append(ComponentInfo(
                name="Ingestion",
                summary=[
                    ComponentField(label="Splitter", value=s.ingestion.splitter),
                    ComponentField(
                        label="Chunking",
                        value=f"{s.ingestion.chunk_size} / {s.ingestion.chunk_overlap}",
                    ),
                ],
                extra={
                    "batch_size": s.ingestion.batch_size,
                },
            ))

        return cards
