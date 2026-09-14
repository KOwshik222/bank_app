"""
Vector Store — wraps Qdrant client in in-memory mode (dev) or server mode (prod).
Provides collection initialization, upsert, and semantic search.
"""

import logging
from typing import Any
from uuid import uuid4

from qdrant_client import QdrantClient
from qdrant_client.http import models

from ai.rag.embeddings import EMBEDDING_DIM, EmbeddingModel

logger = logging.getLogger(__name__)

COLLECTION_NAME = "banking_knowledge_base"


class VectorStore:
    """Manages document vector indexing and similarity search with Qdrant."""

    def __init__(self, location: str = ":memory:"):
        self.client = QdrantClient(location=location)
        self.collection_name = COLLECTION_NAME
        self.embedding_model = EmbeddingModel()
        self._ensure_collection()

    def _ensure_collection(self) -> None:
        """Create Qdrant collection if it does not already exist."""
        collections = self.client.get_collections().collections
        exists = any(c.name == self.collection_name for c in collections)
        if not exists:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(
                    size=EMBEDDING_DIM,
                    distance=models.Distance.COSINE,
                ),
            )
            logger.info(f"Created Qdrant collection: {self.collection_name}")

    def upsert_chunks(self, chunks: list[dict[str, Any]]) -> int:
        """Embed and upsert chunks into Qdrant collection."""
        if not chunks:
            return 0

        texts = [c["content"] for c in chunks]
        embeddings = self.embedding_model.embed_batch(texts)

        points = []
        for i, chunk in enumerate(chunks):
            point_id = str(uuid4())
            points.append(
                models.PointStruct(
                    id=point_id,
                    vector=embeddings[i],
                    payload=chunk,
                )
            )

        self.client.upsert(
            collection_name=self.collection_name,
            points=points,
        )
        logger.info(f"Upserted {len(points)} chunks into {self.collection_name}")
        return len(points)

    def search(
        self,
        query: str,
        limit: int = 5,
        category: str | None = None,
        score_threshold: float = 0.25,
    ) -> list[dict[str, Any]]:
        """Search vector store for relevant document chunks."""
        query_vector = self.embedding_model.embed_text(query)

        filter_condition = None
        if category:
            filter_condition = models.Filter(
                must=[
                    models.FieldCondition(
                        key="category",
                        match=models.MatchValue(value=category),
                    )
                ]
            )

        if hasattr(self.client, "query_points"):
            response = self.client.query_points(
                collection_name=self.collection_name,
                query=query_vector,
                limit=limit,
                query_filter=filter_condition,
                score_threshold=score_threshold,
            )
            search_results = response.points
        else:
            search_results = getattr(self.client, "search")(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=limit,
                query_filter=filter_condition,
                score_threshold=score_threshold,
            )

        results = []
        for hit in search_results:
            item = dict(hit.payload or {})
            item["score"] = round(float(hit.score), 4)
            results.append(item)

        return results

    def count(self) -> int:
        """Count total vectors in collection."""
        res = self.client.count(collection_name=self.collection_name)
        return res.count
