import pytest
from pathlib import Path
from ai.rag.chunker import chunk_markdown_file, DocumentChunk
from ai.rag.embeddings import EmbeddingModel
from ai.rag.vector_store import VectorStore
from ai.rag.retriever import KnowledgeRetriever
from ai.rag.ingest import ingest_knowledge_base

def test_markdown_chunker(tmp_path: Path):
    doc_file = tmp_path / "runbook_db_pool.md"
    doc_file.write_text("""# Database Connection Pool Exhaustion Runbook

## Overview
When the connection pool for the primary banking PostgreSQL database reaches 100% capacity, all incoming HTTP payment requests block and fail with timeout exceptions.

## Diagnostics
Run the diagnostic query:
```sql
SELECT count(*), state FROM pg_stat_activity GROUP BY state;
```

## Remediation
1. Terminate idle in transaction connections.
2. Restart the connection pooler.
3. Roll back any recent deployment with unclosed sessions.
""", encoding="utf-8")

    chunks = chunk_markdown_file(doc_file)
    assert len(chunks) >= 1
    for chunk in chunks:
        assert isinstance(chunk, DocumentChunk)
        assert chunk.source_file == "runbook_db_pool.md"
        assert len(chunk.content) > 0

def test_embeddings_generator():
    model = EmbeddingModel()
    emb = model.embed_text("PostgreSQL connection pool exhaustion")
    assert isinstance(emb, list)
    assert len(emb) == 384
    assert any(x != 0 for x in emb)

def test_knowledge_retriever():
    ingest_knowledge_base()
    retriever = KnowledgeRetriever()
    results = retriever.retrieve("PostgreSQL database connection pool exhaustion", limit=3)
    assert isinstance(results, list)
    assert len(results) > 0
    top = results[0]
    assert "title" in top
    assert "citation" in top
    assert "relevance_score" in top
