"""
Retriever module — semantic retrieval with source attribution and metadata filtering.
Provides specialized retrieval functions for AI agents.
"""

import logging
from typing import Any

from ai.rag.vector_store import VectorStore

logger = logging.getLogger(__name__)

# Global singleton instance for shared in-memory vector store
_global_vector_store: VectorStore | None = None


def get_vector_store() -> VectorStore:
    """Retrieve or initialize the global vector store instance."""
    global _global_vector_store
    if _global_vector_store is None:
        _global_vector_store = VectorStore()
    return _global_vector_store


class KnowledgeRetriever:
    """Provides high-level retrieval methods for AI investigation agents."""

    def __init__(self, vector_store: VectorStore | None = None):
        self.vector_store = vector_store or get_vector_store()

    def retrieve(
        self,
        query: str,
        limit: int = 5,
        category: str | None = None,
        min_score: float = 0.20,
    ) -> list[dict[str, Any]]:
        """Retrieve relevant knowledge base passages with citation metadata."""
        hits = self.vector_store.search(
            query=query,
            limit=limit,
            category=category,
            score_threshold=min_score,
        )

        formatted_results = []
        for hit in hits:
            formatted_results.append({
                "title": hit.get("title", "Untitled Document"),
                "section": hit.get("section", "General"),
                "category": hit.get("category", "General"),
                "source_file": hit.get("source_file", "unknown.md"),
                "content": hit.get("content", ""),
                "relevance_score": hit.get("score", 0.0),
                "citation": f"[{hit.get('title')}] ({hit.get('source_file')}#{hit.get('section')})",
            })

        return formatted_results

    def search_runbooks(self, query: str, limit: int = 3) -> list[dict[str, Any]]:
        """Search runbooks for troubleshooting steps and remediation instructions."""
        return self.retrieve(query, limit=limit, category="runbooks")

    def search_historical_incidents(self, query: str, limit: int = 3) -> list[dict[str, Any]]:
        """Search past resolved incidents to find similar root causes and previous fixes."""
        return self.retrieve(query, limit=limit, category="historical_incidents")

    def search_api_docs(self, query: str, limit: int = 3) -> list[dict[str, Any]]:
        """Search microservice API specifications and health check standards."""
        return self.retrieve(query, limit=limit, category="api_docs")

    def search_infra_guides(self, query: str, limit: int = 3) -> list[dict[str, Any]]:
        """Search infrastructure guides (Kafka, network, CPU, memory)."""
        return self.retrieve(query, limit=limit, category="infra_guides")
