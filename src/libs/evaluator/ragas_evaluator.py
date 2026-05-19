"""Ragas-based evaluator for RAG quality assessment.

This evaluator wraps the Ragas framework to compute LLM-as-Judge metrics:
- Faithfulness: Does the answer stick to the retrieved context?
- Answer Relevancy: Is the answer relevant to the query?
- Context Precision: Are the retrieved chunks relevant and well-ordered?

Design Principles:
- Pluggable: Implements BaseEvaluator interface, swappable via factory.
- Config-Driven: LLM/Embedding backend read from settings.yaml.
- Graceful Degradation: Clear ImportError if ragas not installed.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Sequence

from src.libs.evaluator.base_evaluator import BaseEvaluator

logger = logging.getLogger(__name__)

# Metric name constants
FAITHFULNESS = "faithfulness"
ANSWER_RELEVANCY = "answer_relevancy"
CONTEXT_PRECISION = "context_precision"

SUPPORTED_METRICS = {FAITHFULNESS, ANSWER_RELEVANCY, CONTEXT_PRECISION}


def _import_ragas() -> None:
    """Validate that ragas is importable, raising a clear error if not."""
    try:
        import ragas  # noqa: F401
    except ImportError as exc:
        raise ImportError(
            "The 'ragas' package is required for RagasEvaluator. "
            "Install it with: pip install ragas datasets"
        ) from exc


class RagasEvaluator(BaseEvaluator):
    """Evaluator that uses the Ragas framework for LLM-as-Judge metrics.

    Ragas does NOT require ground-truth labels.  It uses an LLM to judge
    the quality of the generated answer against the retrieved context.

    Supported metrics:
        - faithfulness: Measures factual consistency with context.
        - answer_relevancy: Measures how relevant the answer is to the query.
        - context_precision: Measures relevance/ordering of retrieved chunks.

    Example::

        evaluator = RagasEvaluator(settings=settings)
        metrics = evaluator.evaluate(
            query="What is RAG?",
            retrieved_chunks=[{"id": "c1", "text": "RAG is ..."}],
            generated_answer="RAG stands for ...",
        )
        # metrics == {"faithfulness": 0.95, "answer_relevancy": 0.88, ...}
    """

    def __init__(
        self,
        settings: Any = None,
        metrics: Optional[Sequence[str]] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize RagasEvaluator.

        Args:
            settings: Application settings (used to configure LLM backend).
            metrics: Metric names to compute. Defaults to all supported.
            **kwargs: Additional parameters (reserved).

        Raises:
            ImportError: If ragas is not installed.
            ValueError: If unsupported metric names are requested.
        """
        _import_ragas()

        self.settings = settings
        self.kwargs = kwargs

        if metrics is None:
            metrics = self._metrics_from_settings(settings)

        normalised = [m.strip().lower() for m in (metrics or [])]
        if not normalised:
            normalised = sorted(SUPPORTED_METRICS)

        unsupported = [m for m in normalised if m not in SUPPORTED_METRICS]
        if unsupported:
            raise ValueError(
                f"Unsupported ragas metrics: {', '.join(unsupported)}. "
                f"Supported: {', '.join(sorted(SUPPORTED_METRICS))}"
            )

        self._metric_names = normalised

    # ── public API ────────────────────────────────────────────────

    def evaluate(
        self,
        query: str,
        retrieved_chunks: List[Any],
        generated_answer: Optional[str] = None,
        ground_truth: Optional[Any] = None,
        trace: Optional[Any] = None,
        **kwargs: Any,
    ) -> Dict[str, float]:
        """Evaluate RAG quality using Ragas LLM-as-Judge metrics.

        Args:
            query: The user query string.
            retrieved_chunks: Retrieved chunks (dicts with 'text' key or strings).
            generated_answer: The generated answer text. Required for Ragas.
            ground_truth: Ignored by Ragas (not needed for LLM-as-Judge).
            trace: Optional TraceContext for observability.
            **kwargs: Additional parameters.

        Returns:
            Dictionary mapping metric names to float scores (0.0 – 1.0).

        Raises:
            ValueError: If query/chunks are invalid or generated_answer is missing.
        """
        self.validate_query(query)

        if not retrieved_chunks:
            return {m: 0.0 for m in self._metric_names}

        self.validate_retrieved_chunks(retrieved_chunks)

        if not generated_answer or not generated_answer.strip():
            raise ValueError(
                "RagasEvaluator requires a non-empty 'generated_answer'. "
                "Ragas uses LLM-as-Judge and needs the answer text to evaluate."
            )

        contexts = self._extract_texts(retrieved_chunks)

        try:
            result = self._run_ragas(query, contexts, generated_answer)
        except Exception as exc:
            logger.error("Ragas evaluation failed: %s", exc, exc_info=True)
            raise RuntimeError(f"Ragas evaluation failed: {exc}") from exc

        return result

    # ── private helpers ───────────────────────────────────────────

    def _run_ragas(
        self,
        query: str,
        contexts: List[str],
        answer: str,
    ) -> Dict[str, float]:
        """Execute Ragas collections metrics and return normalised scores.

        Ragas 0.4+ collections metrics use per-metric ``score()`` instead of
        the legacy ``evaluate()`` pipeline.  Each metric has its own signature:
        - Faithfulness / ContextPrecision: (user_input, response, retrieved_contexts)
        - AnswerRelevancy: (user_input, response)
        """
        from ragas.metrics.collections import (
            Faithfulness,
            AnswerRelevancy,
            ContextPrecisionWithoutReference,
        )

        # Build LLM / Embedding wrappers from settings
        llm, embeddings = self._build_wrappers()

        scores: Dict[str, float] = {}

        for metric_name in self._metric_names:
            if metric_name == FAITHFULNESS:
                m = Faithfulness(llm=llm)
                result = m.score(
                    user_input=query, response=answer, retrieved_contexts=contexts,
                )
            elif metric_name == ANSWER_RELEVANCY:
                m = AnswerRelevancy(llm=llm, embeddings=embeddings)
                result = m.score(user_input=query, response=answer)
            elif metric_name == CONTEXT_PRECISION:
                m = ContextPrecisionWithoutReference(llm=llm)
                result = m.score(
                    user_input=query, response=answer, retrieved_contexts=contexts,
                )
            else:
                continue

            scores[metric_name] = float(result.value) if result.value is not None else 0.0

        return scores

    # Providers whose APIs are OpenAI-compatible but run at a
    # well-known default base URL (no custom base_url in settings).
    _DEFAULT_OPENAI_COMPAT_BASE: Dict[str, str] = {
        "deepseek": "https://api.deepseek.com/v1",
        "ollama": "http://localhost:11434/v1",
    }

    def _build_wrappers(self) -> tuple:
        """Build Ragas LLM and Embedding wrappers from project settings.

        Uses Ragas 0.4+ native API (InstructorLLM + OpenAIEmbeddings)
        instead of deprecated LangchainLLMWrapper.

        Returns:
            Tuple of (llm_wrapper, embeddings_wrapper).
        """
        from ragas.llms import llm_factory
        from ragas.embeddings import OpenAIEmbeddings

        if self.settings is None:
            raise ValueError("Settings required to create LLM for Ragas evaluation")

        llm = self._make_ragas_llm(llm_factory)
        embeddings = self._make_ragas_embeddings(OpenAIEmbeddings)

        return llm, embeddings

    # ── per-client helpers ───────────────────────────────────────────

    @staticmethod
    def _resolve_base_url(provider: str, custom_base_url: Optional[str]) -> str:
        """Return the effective base_url for an OpenAI-compatible provider."""
        if custom_base_url:
            return custom_base_url
        return RagasEvaluator._DEFAULT_OPENAI_COMPAT_BASE.get(provider, "")

    @staticmethod
    def _build_llm_client(api_key: Optional[str], base_url: str, **kwargs: Any):
        """Create an AsyncOpenAI client for OpenAI-compatible providers."""
        from openai import AsyncOpenAI

        init_kwargs: dict = {"api_key": api_key}
        if base_url:
            init_kwargs["base_url"] = base_url
        init_kwargs.update(kwargs)
        return AsyncOpenAI(**init_kwargs)

    def _make_ragas_llm(self, llm_factory: Any) -> Any:
        """Build a Ragas LLM wrapper for the configured LLM provider."""
        from openai import AsyncAzureOpenAI

        llm_cfg = self.settings.llm
        provider = llm_cfg.provider.lower()
        azure_endpoint = getattr(llm_cfg, "azure_endpoint", None)

        # ── Azure path ──
        use_azure = (
            provider == "azure"
            or (provider == "openai" and azure_endpoint)
        )
        if use_azure:
            client = AsyncAzureOpenAI(
                api_key=llm_cfg.api_key,
                azure_endpoint=azure_endpoint,
                api_version=getattr(llm_cfg, "api_version", None) or "2024-02-15-preview",
            )
            return llm_factory(llm_cfg.model, client=client, max_tokens=8192)

        # ── OpenAI-compatible path (openai / deepseek / ollama / …) ──
        base_url = self._resolve_base_url(
            provider,
            getattr(llm_cfg, "base_url", None),
        )
        client = self._build_llm_client(llm_cfg.api_key, base_url)
        return llm_factory(llm_cfg.model, client=client, max_tokens=8192)

    def _make_ragas_embeddings(self, OpenAIEmbeddings: type) -> Any:
        """Build Ragas OpenAIEmbeddings wrapper for the configured provider."""
        from openai import AsyncAzureOpenAI

        emb_cfg = self.settings.embedding
        provider = emb_cfg.provider.lower()
        azure_endpoint = getattr(emb_cfg, "azure_endpoint", None)

        # ── Azure path ──
        use_azure = (
            provider == "azure"
            or (provider == "openai" and azure_endpoint)
        )
        if use_azure:
            client = AsyncAzureOpenAI(
                api_key=emb_cfg.api_key,
                azure_endpoint=azure_endpoint,
                api_version=getattr(emb_cfg, "api_version", None) or "2024-02-15-preview",
            )
            return OpenAIEmbeddings(model=emb_cfg.model, client=client)

        # ── OpenAI-compatible path ──
        base_url = self._resolve_base_url(
            provider,
            getattr(emb_cfg, "base_url", None),
        )
        client = self._build_llm_client(emb_cfg.api_key, base_url)
        return OpenAIEmbeddings(model=emb_cfg.model, client=client)

    def _extract_texts(self, chunks: List[Any]) -> List[str]:
        """Extract text strings from various chunk representations.

        Args:
            chunks: List of chunk dicts, strings, or objects with .text.

        Returns:
            List of text strings.
        """
        texts: List[str] = []
        for chunk in chunks:
            if isinstance(chunk, str):
                texts.append(chunk)
            elif isinstance(chunk, dict):
                text = chunk.get("text") or chunk.get("content") or chunk.get("page_content", "")
                texts.append(str(text))
            elif hasattr(chunk, "text"):
                texts.append(str(getattr(chunk, "text")))
            else:
                texts.append(str(chunk))
        return texts

    def _metrics_from_settings(self, settings: Any) -> List[str]:
        """Extract metrics list from settings if available."""
        if settings is None:
            return []
        evaluation = getattr(settings, "evaluation", None)
        if evaluation is None:
            return []
        raw_metrics = getattr(evaluation, "metrics", None)
        if raw_metrics is None:
            return []
        # Filter to only ragas-supported metrics
        return [m for m in raw_metrics if m.lower() in SUPPORTED_METRICS]
