"""Tests for G1 – Dashboard ConfigService and page imports.

Covers:
- ConfigService.get_component_cards() returns expected components
- app.py and pages/overview.py are importable without error
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

from src.observability.dashboard.services.config_service import (
    ConfigService,
)


# ── Fake Settings ────────────────────────────────────────────────────

def _fake_settings():
    """Build a mock Settings object with realistic field values."""
    s = MagicMock()
    s.llm.provider = "azure_openai"
    s.llm.model = "gpt-4o"
    s.llm.temperature = 0.0
    s.llm.max_tokens = 4096

    s.embedding.provider = "azure_openai"
    s.embedding.model = "text-embedding-ada-002"
    s.embedding.dimensions = 1536

    s.vector_store.provider = "chroma"
    s.vector_store.collection_name = "default"
    s.vector_store.persist_directory = "data/db/chroma"

    s.retrieval.dense_top_k = 20
    s.retrieval.sparse_top_k = 20
    s.retrieval.fusion_top_k = 10
    s.retrieval.query_orchestration.enabled = True
    s.retrieval.query_orchestration.planner_provider = "llm"
    s.retrieval.query_orchestration.mode = "auto"
    s.retrieval.query_orchestration.max_sub_queries = 4
    s.retrieval.query_orchestration.parallel_sub_queries = True
    s.retrieval.query_orchestration.merge_fusion = "rrf"

    s.rerank.enabled = True
    s.rerank.provider = "llm"
    s.rerank.model = "gpt-4o"
    s.rerank.top_k = 5

    s.vision_llm.enabled = True
    s.vision_llm.provider = "azure_openai"
    s.vision_llm.model = "gpt-4o"
    s.vision_llm.max_image_size = 2048

    s.ingestion.splitter = "recursive"
    s.ingestion.chunk_size = 1000
    s.ingestion.chunk_overlap = 200
    s.ingestion.batch_size = 100

    return s


def _summary_map(card) -> dict[str, str]:
    return {field.label: field.value for field in card.summary}


# ── Tests ────────────────────────────────────────────────────────────


class TestConfigService:
    """Verify ConfigService produces component cards."""

    @patch("src.observability.dashboard.services.config_service.load_settings")
    def test_get_component_cards_returns_list(self, mock_load) -> None:
        mock_load.return_value = _fake_settings()
        svc = ConfigService("config/settings.yaml")
        cards = svc.get_component_cards()
        assert isinstance(cards, list)
        assert len(cards) >= 5  # LLM, Embedding, VectorStore, Retrieval, Reranker

    @patch("src.observability.dashboard.services.config_service.load_settings")
    def test_llm_card(self, mock_load) -> None:
        mock_load.return_value = _fake_settings()
        svc = ConfigService()
        cards = svc.get_component_cards()
        llm = next(c for c in cards if c.name == "LLM")
        assert _summary_map(llm) == {
            "Provider": "azure_openai",
            "Model": "gpt-4o",
        }

    @patch("src.observability.dashboard.services.config_service.load_settings")
    def test_embedding_card(self, mock_load) -> None:
        mock_load.return_value = _fake_settings()
        svc = ConfigService()
        cards = svc.get_component_cards()
        emb = next(c for c in cards if c.name == "Embedding")
        assert _summary_map(emb)["Provider"] == "azure_openai"
        assert emb.extra["dimensions"] == 1536

    @patch("src.observability.dashboard.services.config_service.load_settings")
    def test_rerank_disabled(self, mock_load) -> None:
        settings = _fake_settings()
        settings.rerank.enabled = False
        mock_load.return_value = settings
        svc = ConfigService()
        cards = svc.get_component_cards()
        reranker = next(c for c in cards if c.name == "Reranker")
        assert reranker.status == "disabled"
        assert _summary_map(reranker) == {"Type": "-", "Top K": "5"}

    @patch("src.observability.dashboard.services.config_service.load_settings")
    def test_query_orchestration_card_present(self, mock_load) -> None:
        mock_load.return_value = _fake_settings()
        svc = ConfigService()
        cards = svc.get_component_cards()
        orchestration = next(c for c in cards if c.name == "Query Orchestration")
        assert orchestration.status == "enabled"
        assert _summary_map(orchestration) == {
            "Planner": "llm",
            "Configured Mode": "auto",
        }
        assert orchestration.extra["max_sub_queries"] == 4
        assert orchestration.extra["merge_fusion (decomposition)"] == "rrf"
        assert orchestration.extra["parallel_sub_queries"] is False  # mode=auto != decomposition

    @patch("src.observability.dashboard.services.config_service.load_settings")
    def test_query_orchestration_parallel_sub_queries_true_when_decomposition(
        self, mock_load
    ) -> None:
        settings = _fake_settings()
        settings.retrieval.query_orchestration.mode = "decomposition"
        settings.retrieval.query_orchestration.parallel_sub_queries = True
        mock_load.return_value = settings
        svc = ConfigService()
        cards = svc.get_component_cards()
        orchestration = next(c for c in cards if c.name == "Query Orchestration")
        assert orchestration.extra["parallel_sub_queries"] is True

    @patch("src.observability.dashboard.services.config_service.load_settings")
    def test_query_orchestration_precedes_retrieval(self, mock_load) -> None:
        mock_load.return_value = _fake_settings()
        svc = ConfigService()
        cards = svc.get_component_cards()
        names = [card.name for card in cards]
        assert names.index("Query Orchestration") < names.index("Retrieval")

    @patch("src.observability.dashboard.services.config_service.load_settings")
    def test_vision_llm_card_present(self, mock_load) -> None:
        mock_load.return_value = _fake_settings()
        svc = ConfigService()
        cards = svc.get_component_cards()
        vision = next(c for c in cards if c.name == "Vision LLM")
        assert vision.status == "enabled"
        assert vision.extra["enabled"] is True

    @patch("src.observability.dashboard.services.config_service.load_settings")
    def test_ingestion_card_present(self, mock_load) -> None:
        mock_load.return_value = _fake_settings()
        svc = ConfigService()
        cards = svc.get_component_cards()
        ingestion = next(c for c in cards if c.name == "Ingestion")
        assert _summary_map(ingestion) == {
            "Splitter": "recursive",
            "Chunking": "1000 / 200",
        }
        assert ingestion.extra["batch_size"] == 100

    @patch("src.observability.dashboard.services.config_service.load_settings")
    def test_vector_store_card_uses_default_collection_label(self, mock_load) -> None:
        mock_load.return_value = _fake_settings()
        svc = ConfigService()
        cards = svc.get_component_cards()
        vector_store = next(c for c in cards if c.name == "Vector Store")
        assert _summary_map(vector_store) == {
            "Engine": "chroma",
            "Default Collection": "default",
        }

    @patch("src.observability.dashboard.services.config_service.load_settings")
    def test_retrieval_card_describes_pipeline_not_provider_model(self, mock_load) -> None:
        mock_load.return_value = _fake_settings()
        svc = ConfigService()
        cards = svc.get_component_cards()
        retrieval = next(c for c in cards if c.name == "Retrieval")
        assert _summary_map(retrieval) == {
            "Pipeline": "hybrid",
            "Rank Fusion": "dense + sparse -> RRF",
        }

    @patch("src.observability.dashboard.services.config_service.load_settings")
    def test_reranker_status_uses_same_enabled_source(self, mock_load) -> None:
        mock_load.return_value = _fake_settings()
        svc = ConfigService()
        cards = svc.get_component_cards()
        reranker = next(c for c in cards if c.name == "Reranker")
        assert reranker.status == "enabled"
        assert reranker.extra["enabled"] is True

    @patch("src.observability.dashboard.services.config_service.load_settings")
    def test_reload_clears_cache(self, mock_load) -> None:
        mock_load.return_value = _fake_settings()
        svc = ConfigService()
        _ = svc.get_component_cards()
        svc.reload()
        assert svc._settings is None


class TestDashboardImports:
    """Verify main app module is importable."""

    def test_config_service_importable(self) -> None:
        from src.observability.dashboard.services.config_service import ConfigService
        assert ConfigService is not None

    def test_overview_importable(self) -> None:
        from src.observability.dashboard.pages import overview
        assert hasattr(overview, "render")

    def test_app_file_exists(self) -> None:
        app_path = Path("src/observability/dashboard/app.py")
        assert app_path.exists()

    def test_start_script_exists(self) -> None:
        script_path = Path("scripts/start_dashboard.py")
        assert script_path.exists()
