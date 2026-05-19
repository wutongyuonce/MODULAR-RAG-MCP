"""Query orchestration planner for expansion and decomposition decisions.

This module decides whether a query should run as:
- direct: use the current single-query retrieval path
- synonym: expand sparse keywords with aliases or synonyms
- decomposition: split into multiple sub-queries for later orchestration
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.core.settings import Settings, resolve_path
from src.core.trace.trace_context import TraceContext
from src.core.types import QueryPlan, SubQueryPlan
from src.libs.llm.base_llm import BaseLLM, Message
from src.libs.llm.llm_factory import LLMFactory


COMMON_SYNONYMS: Dict[str, List[str]] = {
    # ── RAG / Retrieval ──
    "rag": ["retrieval augmented generation", "检索增强生成", "rag system"],
    "检索": ["search", "retrieval", "query"],
    "召回": ["recall", "retrieval", "检索", "candidate retrieval"],
    "混合检索": ["hybrid search", "dense sparse fusion", "bm25 dense"],
    "hybrid search": ["混合检索", "dense + sparse", "bm25 + embedding"],
    "bm25": ["sparse retrieval", "稀疏检索", "keyword search", "bm25 algorithm"],
    "dense": ["embedding", "vector", "语义", "稠密向量"],
    "sparse": ["bm25", "keyword", "tf-idf", "稀疏检索"],
    "vector": ["embedding", "向量", "dense"],
    "chunk": ["document chunk", "片段", "文档块", "text fragment"],
    "rerank": ["re-ranking", "重排序", "精排", "second stage ranking"],
    "re-ranking": ["rerank", "重排序", "精排"],
    "fusion": ["融合", "merge", "rrf", "rank fusion"],
    "rrf": ["reciprocal rank fusion", "融合排序"],
    # ── LLM / Model ──
    "llm": ["large language model", "大语言模型", "大模型", "language model"],
    "大模型": ["llm", "large language model", "大语言模型", "foundation model"],
    "模型": ["model", "llm", "neural network"],
    "gpt": ["gpt-4", "openai gpt", "generative pre-trained transformer"],
    "deepseek": ["deep seek", "deepseek ai", "深度求索"],
    "ollama": ["local llm", "本地模型", "本地部署"],
    "openai": ["open ai", "openai api"],
    "azure": ["azure openai", "microsoft azure", "微软云"],
    "推理": ["inference", "reasoning", "生成"],
    "inference": ["推理", "reasoning", "prediction"],
    "embedding": ["vector embedding", "向量嵌入", "向量化", "text embedding"],
    "向量": ["vector", "embedding", "representation"],
    # ── MCP / Protocol ──
    "mcp": ["model context protocol", "mcp server", "mcp 协议"],
    "agent": ["ai agent", "智能体", "tool calling", "代理"],
    "tool": ["function", "api", "工具", "接口"],
    "api": ["interface", "接口", "endpoint", "api endpoint"],
    "server": ["服务端", "backend", "service"],
    "client": ["客户端", "frontend", "consumer"],
    # ── Ingestion / Pipeline ──
    "摄入": ["ingestion", "import", "索引", "数据导入"],
    "ingestion": ["摄入", "indexing", "数据摄取", "import"],
    "pipeline": ["流水线", "管道", "workflow", "流程"],
    "pdf": ["document", "文件", "portable document format", "文档"],
    "markdown": ["md", "markdown格式", "文本"],
    "splitter": ["chunker", "切分器", "text splitter", "分块"],
    # ── Evaluation ──
    "评估": ["evaluation", "评测", "benchmark", "assessment"],
    "evaluation": ["评估", "评测", "benchmark", "assessment"],
    "ragas": ["rag evaluation", "rag 评估框架"],
    "faithfulness": ["真实性", "准确性", "一致性", "factuality"],
    "precision": ["准确率", "精确度", "查准率"],
    "recall": ["召回率", "查全率", "hit rate"],
    "mrr": ["mean reciprocal rank", "平均倒数排名"],
    # ── Storage / Database ──
    "chroma": ["chromadb", "vector database", "向量数据库", "chroma db"],
    "chromadb": ["chroma", "vector store", "向量存储"],
    "向量数据库": ["vector database", "chroma", "qdrant", "milvus"],
    "vector store": ["向量存储", "vector database", "chroma"],
    "sqlite": ["sqlite3", "轻量数据库", "嵌入式数据库"],
    # ── Architecture / Design ──
    "可插拔": ["pluggable", "plugin", "模块化", "可替换"],
    "pluggable": ["可插拔", "plugin-based", "模块化", "modular"],
    "模块化": ["modular", "可插拔", "component-based", "可替换"],
    "工厂模式": ["factory pattern", "factory method", "工厂方法"],
    "抽象": ["abstraction", "interface", "接口"],
    "配置": ["configuration", "settings", "config", "yaml"],
    "config": ["configuration", "settings", "配置", "yaml config"],
    "dashboard": ["面板", "管理平台", "streamlit", "可视化"],
    "streamlit": ["dashboard", "面板", "web ui", "可视化"],
    "trace": ["追踪", "日志", "log", "observability"],
    "可观测": ["observability", "trace", "logging", "monitoring"],
    # ── General AI/ML ──
    "transformer": ["transformer架构", "attention", "自注意力"],
    "prompt": ["提示词", "指令", "prompt engineering", "提示"],
    "token": ["令牌", "tokenizer", "词元"],
    "多模态": ["multimodal", "vision", "image text", "图文"],
    "multimodal": ["多模态", "vision language", "image caption"],
    "vision": ["视觉", "image", "multimodal", "图片"],
    "图片": ["image", "picture", "figure", "diagram", "截图"],
    "clip": ["contrastive language image pre-training"],
    "cross encoder": ["cross-encoder", "reranker", "cross encoder model"],
    "bi encoder": ["bi-encoder", "dual encoder", "双塔模型"],
    # ── Developer / DevOps ──
    "docker": ["container", "容器", "dockerfile"],
    "ci/cd": ["continuous integration", "持续集成", "pipeline"],
    "测试": ["test", "testing", "unit test", "pytest"],
    "bug": ["defect", "issue", "错误", "problem", "问题"],
    "部署": ["deployment", "deploy", "上线", "release"],
    "github": ["git", "repository", "代码库", "仓库"],
    # ── Programming ──
    "python": ["python3", "py", "python语言"],
    "javascript": ["js", "ecmascript", "nodejs"],
    "typescript": ["ts", "typed javascript"],
    "cpp": ["c++", "c plus plus"],
    "c++": ["cpp", "c plus plus"],
}

DECOMPOSITION_HINTS = (
    "对比",
    "比较",
    "区别",
    "差异",
    "分别",
    "以及",
    "并且",
    "同时",
    "优缺点",
)


class QueryPlanningError(RuntimeError):
    """Raised when planner execution or parsing fails."""


class QueryOrchestrator:
    """Builds a structured query plan for downstream retrieval orchestration."""

    def __init__(
        self,
        settings: Settings,
        llm: Optional[BaseLLM] = None,
        prompt_path: Optional[str] = None,
    ) -> None:
        self.settings = settings
        self.config = settings.retrieval.query_orchestration
        self._llm = llm
        self.prompt_path = prompt_path or str(
            resolve_path("config/prompts/query_orchestration_planner.txt")
        )
        self._prompt_template: Optional[str] = None

    @property
    def llm(self) -> BaseLLM:
        """Lazy-load the planner LLM only when needed."""
        if self._llm is None:
            self._llm = LLMFactory.create(self.settings)
        return self._llm

    def plan(
        self,
        query: str,
        keywords: Optional[List[str]] = None,
        filters: Optional[Dict[str, Any]] = None,
        top_k: Optional[int] = None,
        collection: Optional[str] = None,
        trace: Optional[TraceContext] = None,
    ) -> QueryPlan:
        """Create a structured plan for a query.

        Falls back to a direct query plan when orchestration is disabled,
        LLM planning fails, or the returned structure is invalid.
        """
        keywords = keywords or []
        filters = filters or {}
        top_k = top_k or self.settings.retrieval.fusion_top_k

        if not query or not query.strip():
            plan = QueryPlan(mode="direct", reason="empty_query", used_fallback=False)
            self._record_trace(trace, plan, query, keywords, filters)
            return plan

        if not self.config.enabled or self.config.mode == "off":
            plan = QueryPlan(
                mode="direct",
                reason="query_orchestration_disabled",
                used_fallback=False,
            )
            self._record_trace(trace, plan, query, keywords, filters)
            return plan

        allowed_modes = self._allowed_modes()
        try:
            if self.config.planner_provider == "rules":
                plan = self._plan_with_rules(query, keywords, allowed_modes)
            else:
                plan = self._plan_with_llm(
                    query=query,
                    keywords=keywords,
                    filters=filters,
                    top_k=top_k,
                    collection=collection,
                    allowed_modes=allowed_modes,
                    trace=trace,
                )
        except Exception as exc:
            plan = QueryPlan(
                mode="direct",
                reason=f"planner_fallback:{type(exc).__name__}",
                used_fallback=True,
            )

        self._record_trace(trace, plan, query, keywords, filters)
        return plan

    def _allowed_modes(self) -> List[str]:
        """Return allowed execution modes based on config."""
        if self.config.mode == "auto":
            return ["direct", "synonym", "decomposition"]
        if self.config.mode == "synonym":
            return ["synonym"]
        if self.config.mode == "decomposition":
            return ["decomposition"]
        return ["direct"]

    def _plan_with_llm(
        self,
        query: str,
        keywords: List[str],
        filters: Dict[str, Any],
        top_k: int,
        collection: Optional[str],
        allowed_modes: List[str],
        trace: Optional[TraceContext],
    ) -> QueryPlan:
        """Run LLM planning and normalize the result."""
        prompt = self._build_planner_prompt(
            query=query,
            keywords=keywords,
            filters=filters,
            top_k=top_k,
            collection=collection,
            allowed_modes=allowed_modes,
        )
        response = self.llm.chat(
            [Message(role="user", content=prompt)],
            trace=trace,
            temperature=0.0,
            max_tokens=self.settings.llm.max_tokens,
            timeout=self.config.planner_timeout_seconds,
        )
        raw_plan = self._parse_llm_response(response.content)
        return self._normalize_plan(raw_plan, query, allowed_modes)

    def _plan_with_rules(
        self,
        query: str,
        keywords: List[str],
        allowed_modes: List[str],
    ) -> QueryPlan:
        """Lightweight deterministic fallback planner."""
        lowered_query = query.lower()

        if "decomposition" in allowed_modes and self._looks_like_decomposition(query):
            sub_queries = self._build_rule_sub_queries(query)
            if sub_queries:
                return QueryPlan(
                    mode="decomposition",
                    reason="rules_detected_multi_intent_query",
                    sub_queries=sub_queries,
                    confidence=0.65,
                    used_fallback=False,
                )

        if "synonym" in allowed_modes:
            expanded_terms = self._collect_rule_expansions(lowered_query, keywords)
            if expanded_terms:
                return QueryPlan(
                    mode="synonym",
                    reason="rules_detected_expandable_terms",
                    expanded_terms=expanded_terms,
                    confidence=0.6,
                    used_fallback=False,
                )

        return QueryPlan(
            mode="direct",
            reason="rules_selected_direct_mode",
            used_fallback=False,
        )

    def _build_planner_prompt(
        self,
        query: str,
        keywords: List[str],
        filters: Dict[str, Any],
        top_k: int,
        collection: Optional[str],
        allowed_modes: List[str],
    ) -> str:
        """Build the prompt for LLM-based planning."""
        template = self._load_prompt_template()
        filters_json = json.dumps(filters, ensure_ascii=False, sort_keys=True)
        collection_value = collection or filters.get("collection") or ""
        return (
            f"{template}\n\n"
            f"Allowed modes: {', '.join(allowed_modes)}\n"
            f"Original query: {query}\n"
            f"Keywords: {json.dumps(keywords, ensure_ascii=False)}\n"
            f"Filters: {filters_json}\n"
            f"Collection: {collection_value}\n"
            f"Top K: {top_k}\n"
        )

    def _load_prompt_template(self) -> str:
        """Load planner prompt from file."""
        if self._prompt_template is not None:
            return self._prompt_template

        prompt_file = Path(self.prompt_path)
        if not prompt_file.exists():
            raise FileNotFoundError(
                f"Query orchestration prompt file not found: {self.prompt_path}"
            )

        self._prompt_template = prompt_file.read_text(encoding="utf-8")
        return self._prompt_template

    def _parse_llm_response(self, response_text: str) -> Dict[str, Any]:
        """Parse raw LLM response into a planning payload."""
        text = response_text.strip()
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

        try:
            parsed = json.loads(text)
        except json.JSONDecodeError as exc:
            raise QueryPlanningError(
                f"Planner response is not valid JSON: {exc}"
            ) from exc

        if not isinstance(parsed, dict):
            raise QueryPlanningError(
                f"Planner response must be a JSON object, got {type(parsed).__name__}"
            )

        return parsed

    def _normalize_plan(
        self,
        payload: Dict[str, Any],
        original_query: str,
        allowed_modes: List[str],
    ) -> QueryPlan:
        """Normalize planner output into a validated QueryPlan."""
        mode = str(payload.get("mode", "direct")).strip().lower()
        if mode not in {"direct", "synonym", "decomposition"}:
            raise QueryPlanningError(f"Unsupported planner mode: {mode}")
        if mode not in allowed_modes:
            raise QueryPlanningError(f"Planner selected disallowed mode: {mode}")

        reason = str(payload.get("reason", "")).strip()
        confidence = payload.get("confidence")
        if confidence is not None and not isinstance(confidence, (int, float)):
            raise QueryPlanningError("Planner confidence must be numeric when provided")

        expanded_terms = payload.get("expanded_terms", [])
        if expanded_terms is None:
            expanded_terms = []
        if not isinstance(expanded_terms, list):
            raise QueryPlanningError("expanded_terms must be a list")
        normalized_terms = [
            str(term).strip()
            for term in expanded_terms
            if str(term).strip()
        ]

        raw_sub_queries = payload.get("sub_queries", [])
        if raw_sub_queries is None:
            raw_sub_queries = []
        if not isinstance(raw_sub_queries, list):
            raise QueryPlanningError("sub_queries must be a list")

        sub_queries: List[SubQueryPlan] = []
        for index, item in enumerate(raw_sub_queries, start=1):
            if isinstance(item, str):
                text = item.strip()
                if text:
                    sub_queries.append(
                        SubQueryPlan(query=text, intent="", order=index)
                    )
                continue
            if not isinstance(item, dict):
                raise QueryPlanningError("Each sub_query must be a string or object")
            query = str(item.get("query", "")).strip()
            if not query:
                continue
            sub_queries.append(
                SubQueryPlan(
                    query=query,
                    intent=str(item.get("intent", "")).strip(),
                    order=int(item.get("order", index)),
                )
            )

        if mode == "synonym" and not normalized_terms:
            raise QueryPlanningError("synonym mode requires expanded_terms")

        if mode == "decomposition":
            if not sub_queries:
                raise QueryPlanningError("decomposition mode requires sub_queries")
            if len(sub_queries) > self.config.max_sub_queries:
                sub_queries = sub_queries[: self.config.max_sub_queries]
            # Remove noop sub-queries that simply repeat the original query.
            sub_queries = [
                item for item in sub_queries if item.query.strip() != original_query.strip()
            ] or [SubQueryPlan(query=original_query.strip(), intent="fallback", order=1)]

        return QueryPlan(
            mode=mode,
            reason=reason,
            expanded_terms=normalized_terms,
            sub_queries=sub_queries,
            confidence=float(confidence) if confidence is not None else None,
            used_fallback=False,
        )

    def _looks_like_decomposition(self, query: str) -> bool:
        """Return True when the query hints at multiple retrieval intents."""
        if any(hint in query for hint in DECOMPOSITION_HINTS):
            return True
        return " vs " in query.lower() or " and " in query.lower()

    def _build_rule_sub_queries(self, query: str) -> List[SubQueryPlan]:
        """Create naive sub-queries from comparison-style queries."""
        cleaned_query = re.sub(r"^(请)?(帮我)?(对比|比较)", "", query).strip()
        cleaned_query = re.sub(r"(的)?(区别|差异|优缺点)\s*$", "", cleaned_query).strip()

        separators = r"以及|并且|同时|和|vs\.?| and "
        parts = [
            part.strip(" ，,。?？")
            for part in re.split(separators, cleaned_query)
            if part.strip()
        ]
        unique_parts: List[str] = []
        for part in parts:
            if part not in unique_parts:
                unique_parts.append(part)

        return [
            SubQueryPlan(query=part, intent="rules_decomposition", order=index)
            for index, part in enumerate(unique_parts[: self.config.max_sub_queries], start=1)
            if len(part) >= 2
        ]

    def _collect_rule_expansions(
        self,
        lowered_query: str,
        keywords: List[str],
    ) -> List[str]:
        """Collect deterministic synonym expansions from common terms."""
        expansions: List[str] = []
        candidates = {lowered_query, *[keyword.lower() for keyword in keywords]}
        for key, values in COMMON_SYNONYMS.items():
            if any(key in candidate for candidate in candidates):
                for value in values:
                    if value not in expansions:
                        expansions.append(value)
        return expansions

    def _record_trace(
        self,
        trace: Optional[TraceContext],
        plan: QueryPlan,
        query: str,
        keywords: List[str],
        filters: Dict[str, Any],
    ) -> None:
        """Record planner output into the query trace when available."""
        if trace is None:
            return
        trace.record_stage(
            "query_orchestration",
            {
                "original_query": query,
                "keywords": keywords,
                "filters": filters,
                "planner_provider": self.config.planner_provider,
                "mode": plan.mode,
                "reason": plan.reason,
                "expanded_terms": plan.expanded_terms,
                "sub_queries": [item.to_dict() for item in plan.sub_queries],
                "confidence": plan.confidence,
                "used_fallback": plan.used_fallback,
            },
        )
