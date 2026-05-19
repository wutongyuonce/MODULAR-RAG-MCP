"""Unit tests for query_knowledge_hub orchestration integration."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

from mcp import types
import pytest

from src.core.response.response_builder import MCPToolResponse
from src.core.types import ProcessedQuery, RetrievalResult
from src.mcp_server.tools.query_knowledge_hub import (
    QueryKnowledgeHubTool,
    query_knowledge_hub_handler,
)


@pytest.mark.asyncio
async def test_execute_includes_orchestration_metadata() -> None:
    """Tool response metadata should include orchestration details from search."""
    settings = SimpleNamespace()
    tool = QueryKnowledgeHubTool(settings=settings)

    search_result = SimpleNamespace(
        results=[
            RetrievalResult(
                chunk_id="chunk_1",
                score=0.95,
                text="Azure OpenAI config",
                metadata={"source_path": "docs/azure.pdf"},
            )
        ],
        used_fallback=False,
        processed_query=ProcessedQuery(
            original_query="比较 Azure 和 OpenAI 的配置差异",
            keywords=["Azure", "OpenAI", "配置", "差异"],
            orchestration_mode="decomposition",
            sub_queries=["Azure 配置步骤", "OpenAI 配置步骤"],
            planner_reason="query contains comparison",
            planner_confidence=0.92,
        ),
        sub_query_results=[
            {
                "query": "Azure 配置步骤",
                "intent": "Azure path",
                "order": 1,
                "result_count": 1,
                "used_fallback": False,
                "dense_error": None,
                "sparse_error": None,
            },
            {
                "query": "OpenAI 配置步骤",
                "intent": "OpenAI path",
                "order": 2,
                "result_count": 0,
                "used_fallback": True,
                "dense_error": None,
                "sparse_error": "sub_query_execution_error: failed",
            },
        ],
    )

    with patch.object(tool, "_ensure_initialized", return_value=None), patch.object(
        tool,
        "_perform_search",
        return_value=search_result,
    ), patch.object(tool, "_apply_rerank", return_value=search_result.results), patch(
        "src.mcp_server.tools.query_knowledge_hub.TraceCollector.collect",
        return_value=None,
    ):
        response = await tool.execute(
            query="比较 Azure 和 OpenAI 的配置差异",
            top_k=5,
            collection="knowledge_hub",
        )

    assert isinstance(response, MCPToolResponse)
    assert response.metadata["orchestration_mode"] == "decomposition"
    assert response.metadata["sub_query_count"] == 2
    assert response.metadata["planner_reason"] == "query contains comparison"
    assert response.metadata["planner_confidence"] == 0.92
    assert response.metadata["used_fallback"] is False
    assert len(response.metadata["sub_queries"]) == 2


@pytest.mark.asyncio
async def test_handler_returns_call_tool_result_with_orchestration_metadata() -> None:
    """Handler should expose orchestration metadata through MCP text payloads."""
    response = MCPToolResponse(
        content="## 检索结果\n\n内容摘要",
        metadata={
            "query": "比较 Azure 和 OpenAI 的配置差异",
            "orchestration_mode": "decomposition",
            "sub_query_count": 2,
            "used_fallback": True,
        },
        is_empty=False,
    )
    fake_tool = Mock()
    fake_tool.execute = AsyncMock(return_value=response)

    with patch(
        "src.mcp_server.tools.query_knowledge_hub.get_tool_instance",
        return_value=fake_tool,
    ):
        result = await query_knowledge_hub_handler(
            query="比较 Azure 和 OpenAI 的配置差异",
            top_k=5,
            collection="knowledge_hub",
        )

    assert isinstance(result, types.CallToolResult)
    assert result.isError is False
    assert result.content
    assert any("检索结果" in getattr(block, "text", "") for block in result.content)
    assert any(
        "orchestration_mode" in getattr(block, "text", "")
        for block in result.content
        if hasattr(block, "text")
    )
