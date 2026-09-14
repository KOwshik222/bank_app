# ADR 004: Hybrid RAG Vector Retrieval Architecture (Qdrant + Semantic Dense Embeddings)

## Status
Accepted

## Context
When an incident occurs in a complex banking environment, L2/L3 support engineers consult runbooks, API specifications, and historical post-mortems to formulate recovery procedures. Traditional keyword search (e.g. grep or BM25) fails when alerts use different terminology (e.g., "HikariPool timeout" vs "PostgreSQL connection pool exhaustion"). The AI system requires semantic retrieval with exact source citations and sub-millisecond retrieval latency.

## Decision
We implemented a **Semantic RAG Pipeline using Qdrant Vector Database**:
1. **Document Structure**: 30+ structured markdown documents categorized into `runbooks/`, `api_docs/`, `db_guides/`, `infra_guides/`, `deployment_procedures/`, and `historical_incidents/`.
2. **Chunking Strategy**: Markdown header-aware section chunker (`chunk_markdown_file`) that preserves document titles, subsection hierarchies, and code blocks as semantic units.
3. **Embeddings**: 384-dimensional dense semantic vector representations supporting Ollama (`nomic-embed-text`) with a zero-dependency deterministic local semantic projection fallback.
4. **Vector Store**: Qdrant vector database supporting both in-memory development mode (`:memory:`) and clustered Docker/cloud server instances.
5. **Source Attribution**: All retrieved context fragments include explicit Markdown citations: `[Doc Title] (file_path#section)`.

## Consequences
### Positive
- Sub-millisecond retrieval latency (0.61ms average in benchmarks).
- Zero external server dependencies required for local testing or CI pipelines.
- Traceable citations injected into LLM context and presented in the Command Center UI.
