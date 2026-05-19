"""Multi-query result merger for decomposition-based retrieval orchestration."""

from __future__ import annotations

from typing import Any, List, Optional

from src.core.query_engine.fusion import RRFFusion
from src.core.types import RetrievalResult


class MultiQueryMerger:
    """Merge multiple sub-query ranking lists into a single ranked result set."""

    def __init__(self, fusion: Optional[RRFFusion] = None) -> None:
        self.fusion = fusion or RRFFusion()

    def merge(
        self,
        ranking_lists: List[List[RetrievalResult]],
        top_k: Optional[int] = None,
        method: str = "rrf",
        trace: Optional[Any] = None,
    ) -> List[RetrievalResult]:
        """Merge sub-query ranking lists with deterministic deduplication."""
        non_empty_lists = [ranking for ranking in ranking_lists if ranking]
        if not non_empty_lists:
            return []
        if len(non_empty_lists) == 1:
            return non_empty_lists[0][:top_k] if top_k is not None else non_empty_lists[0]

        if method == "weighted_rrf":
            weights = self._build_weights(len(non_empty_lists))
            return self.fusion.fuse_with_weights(
                non_empty_lists,
                weights=weights,
                top_k=top_k,
                trace=trace,
            )

        return self.fusion.fuse(non_empty_lists, top_k=top_k, trace=trace)

    def _build_weights(self, count: int) -> List[float]:
        """Build stable descending weights for weighted RRF."""
        if count <= 1:
            return [1.0]
        return [max(0.6, 1.0 - (index * 0.1)) for index in range(count)]

