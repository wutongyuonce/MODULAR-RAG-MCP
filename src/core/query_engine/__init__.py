"""
Query Engine Module.

This package contains the hybrid search engine components:
- Query preprocessing
- Dense retrieval (embedding-based)
- Sparse retrieval (BM25)
- Result fusion (RRF)
- Reranking
"""

from src.core.query_engine.query_processor import (
    QueryProcessor,
    QueryProcessorConfig,
    create_query_processor,
    DEFAULT_STOPWORDS,
    CHINESE_STOPWORDS,
    ENGLISH_STOPWORDS,
)
from src.core.query_engine.dense_retriever import (
    DenseRetriever,
    create_dense_retriever,
)
from src.core.query_engine.sparse_retriever import (
    SparseRetriever,
    create_sparse_retriever,
)
from src.core.query_engine.fusion import (
    RRFFusion,
    rrf_score,
)
from src.core.query_engine.hybrid_search import (
    HybridSearch,
    HybridSearchConfig,
    HybridSearchResult,
    create_hybrid_search,
)
from src.core.query_engine.query_orchestrator import (
    QueryOrchestrator,
    QueryPlanningError,
)
from src.core.query_engine.multi_query_merger import MultiQueryMerger

__all__ = [
    "QueryProcessor",
    "QueryProcessorConfig",
    "create_query_processor",
    "DEFAULT_STOPWORDS",
    "CHINESE_STOPWORDS",
    "ENGLISH_STOPWORDS",
    "DenseRetriever",
    "create_dense_retriever",
    "SparseRetriever",
    "create_sparse_retriever",
    "RRFFusion",
    "rrf_score",
    "HybridSearch",
    "HybridSearchConfig",
    "HybridSearchResult",
    "create_hybrid_search",
    "QueryOrchestrator",
    "QueryPlanningError",
    "MultiQueryMerger",
]
