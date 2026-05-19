"""Tests for query orchestration planner."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, List, Optional

import pytest

from src.core.query_engine.query_orchestrator import (
    QueryOrchestrator,
    QueryPlanningError,
)
from src.core.settings import (
    EmbeddingSettings,
    EvaluationSettings,
    LLMSettings,
    ObservabilitySettings,
    QueryOrchestrationSettings,
    RerankSettings,
    RetrievalSettings,
    Settings,
    VectorStoreSettings,
)
from src.core.trace.trace_context import TraceContext
from src.libs.llm.base_llm import BaseLLM, ChatResponse, Message


class MockLLM(BaseLLM):
    """Mock LLM for query planner testing."""

    def __init__(self, response_content: str) -> None:
        self.response_content = response_content
        self.last_messages: Optional[List[Message]] = None
        self.call_count = 0

    def chat(
        self,
        messages: List[Message],
        trace: Optional[Any] = None,
        **kwargs: Any,
    ) -> ChatResponse:
        self.call_count += 1
        self.last_messages = messages
        return ChatResponse(content=self.response_content, model="mock-model")


def make_settings(
    *,
    enabled: bool = True,
    mode: str = "auto",
    planner_provider: str = "llm",
) -> Settings:
    """Create test settings with query orchestration enabled."""
    return Settings(
        llm=LLMSettings(
            provider="openai",
            model="gpt-4o-mini",
            temperature=0.0,
            max_tokens=1024,
        ),
        embedding=EmbeddingSettings(
            provider="openai",
            model="text-embedding-3-small",
            dimensions=1536,
        ),
        vector_store=VectorStoreSettings(
            provider="chroma",
            persist_directory="./data/db/chroma",
            collection_name="knowledge_hub",
        ),
        retrieval=RetrievalSettings(
            dense_top_k=20,
            sparse_top_k=20,
            fusion_top_k=10,
            rrf_k=60,
            query_orchestration=QueryOrchestrationSettings(
                enabled=enabled,
                planner_provider=planner_provider,
                mode=mode,
                max_sub_queries=4,
                parallel_sub_queries=True,
                merge_fusion="rrf",
                fallback_to_direct=True,
                planner_timeout_seconds=8.0,
            ),
        ),
        rerank=RerankSettings(
            enabled=False,
            provider="none",
            model="none",
            top_k=5,
        ),
        evaluation=EvaluationSettings(
            enabled=False,
            provider="custom",
            metrics=["hit_rate"],
        ),
        observability=ObservabilitySettings(
            log_level="INFO",
            trace_enabled=True,
            trace_file="./logs/traces.jsonl",
            structured_logging=True,
        ),
    )


class TestQueryOrchestrator:
    """Test suite for query planner behavior."""

    def test_returns_direct_when_disabled(self, tmp_path: Path) -> None:
        prompt_file = tmp_path / "planner.txt"
        prompt_file.write_text("Return JSON", encoding="utf-8")

        orchestrator = QueryOrchestrator(
            settings=make_settings(enabled=False),
            llm=MockLLM("{}"),
            prompt_path=str(prompt_file),
        )

        plan = orchestrator.plan("如何配置 Azure OpenAI？", keywords=["Azure", "OpenAI"])

        assert plan.mode == "direct"
        assert plan.reason == "query_orchestration_disabled"
        assert plan.used_fallback is False

    def test_rules_mode_uses_synonym_expansion(self, tmp_path: Path) -> None:
        prompt_file = tmp_path / "planner.txt"
        prompt_file.write_text("Return JSON", encoding="utf-8")

        orchestrator = QueryOrchestrator(
            settings=make_settings(planner_provider="rules", mode="auto"),
            prompt_path=str(prompt_file),
        )

        plan = orchestrator.plan("RAG 如何提升回答质量？", keywords=["RAG", "回答质量"])

        assert plan.mode == "synonym"
        assert "检索增强生成" in plan.expanded_terms
        assert plan.used_fallback is False

    def test_rules_mode_uses_decomposition_for_comparison(self, tmp_path: Path) -> None:
        prompt_file = tmp_path / "planner.txt"
        prompt_file.write_text("Return JSON", encoding="utf-8")

        orchestrator = QueryOrchestrator(
            settings=make_settings(planner_provider="rules", mode="auto"),
            prompt_path=str(prompt_file),
        )

        plan = orchestrator.plan(
            "比较 Azure OpenAI 和 OpenAI API 的配置差异",
            keywords=["Azure", "OpenAI", "配置", "差异"],
        )

        assert plan.mode == "decomposition"
        assert len(plan.sub_queries) >= 2
        assert all(item.query for item in plan.sub_queries)

    def test_llm_mode_parses_valid_synonym_plan(self, tmp_path: Path) -> None:
        prompt_file = tmp_path / "planner.txt"
        prompt_file.write_text("Return JSON", encoding="utf-8")
        llm = MockLLM(
            json.dumps(
                {
                    "mode": "synonym",
                    "reason": "query includes acronym",
                    "expanded_terms": ["检索增强生成", "retrieval augmented generation"],
                    "sub_queries": [],
                    "confidence": 0.87,
                },
                ensure_ascii=False,
            )
        )

        orchestrator = QueryOrchestrator(
            settings=make_settings(planner_provider="llm", mode="auto"),
            llm=llm,
            prompt_path=str(prompt_file),
        )

        plan = orchestrator.plan("RAG 是什么？", keywords=["RAG"])

        assert plan.mode == "synonym"
        assert plan.reason == "query includes acronym"
        assert plan.expanded_terms == ["检索增强生成", "retrieval augmented generation"]
        assert plan.confidence == 0.87
        assert llm.call_count == 1
        assert llm.last_messages is not None
        assert "Allowed modes: direct, synonym, decomposition" in llm.last_messages[0].content

    def test_llm_mode_parses_decomposition_sub_queries(self, tmp_path: Path) -> None:
        prompt_file = tmp_path / "planner.txt"
        prompt_file.write_text("Return JSON", encoding="utf-8")
        llm = MockLLM(
            """```json
            {
              "mode": "decomposition",
              "reason": "query contains comparison",
              "expanded_terms": [],
              "sub_queries": [
                {"query": "Azure OpenAI 配置步骤", "intent": "Azure path", "order": 1},
                {"query": "OpenAI API 配置步骤", "intent": "OpenAI path", "order": 2}
              ],
              "confidence": 0.91
            }
            ```"""
        )

        orchestrator = QueryOrchestrator(
            settings=make_settings(planner_provider="llm", mode="auto"),
            llm=llm,
            prompt_path=str(prompt_file),
        )

        plan = orchestrator.plan("比较 Azure OpenAI 和 OpenAI API 的配置差异")

        assert plan.mode == "decomposition"
        assert len(plan.sub_queries) == 2
        assert plan.sub_queries[0].query == "Azure OpenAI 配置步骤"
        assert plan.sub_queries[1].intent == "OpenAI path"

    def test_invalid_llm_json_falls_back_to_direct(self, tmp_path: Path) -> None:
        prompt_file = tmp_path / "planner.txt"
        prompt_file.write_text("Return JSON", encoding="utf-8")
        llm = MockLLM("not-json")

        orchestrator = QueryOrchestrator(
            settings=make_settings(planner_provider="llm", mode="auto"),
            llm=llm,
            prompt_path=str(prompt_file),
        )

        plan = orchestrator.plan("RAG 是什么？")

        assert plan.mode == "direct"
        assert plan.used_fallback is True
        assert plan.reason.startswith("planner_fallback:")

    def test_parse_response_rejects_non_object(self, tmp_path: Path) -> None:
        prompt_file = tmp_path / "planner.txt"
        prompt_file.write_text("Return JSON", encoding="utf-8")
        orchestrator = QueryOrchestrator(
            settings=make_settings(planner_provider="llm", mode="auto"),
            llm=MockLLM("{}"),
            prompt_path=str(prompt_file),
        )

        with pytest.raises(QueryPlanningError, match="JSON object"):
            orchestrator._parse_llm_response('["not-an-object"]')

    def test_trace_records_query_orchestration_stage(self, tmp_path: Path) -> None:
        prompt_file = tmp_path / "planner.txt"
        prompt_file.write_text("Return JSON", encoding="utf-8")

        orchestrator = QueryOrchestrator(
            settings=make_settings(planner_provider="rules", mode="auto"),
            prompt_path=str(prompt_file),
        )
        trace = TraceContext(trace_type="query")

        plan = orchestrator.plan(
            "RAG 如何提升回答质量？",
            keywords=["RAG", "回答质量"],
            filters={"collection": "docs"},
            trace=trace,
        )

        stage = trace.get_stage_data("query_orchestration")
        assert plan.mode == "synonym"
        assert stage is not None
        assert stage["mode"] == "synonym"
        assert stage["filters"] == {"collection": "docs"}
        assert stage["expanded_terms"]
