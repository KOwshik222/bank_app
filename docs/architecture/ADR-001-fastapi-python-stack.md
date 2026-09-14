# ADR 001: Selection of FastAPI & Python Monorepo for Unified Banking AI Platform

## Status
Accepted

## Context
A production-grade AI incident resolution platform for banking systems requires tight integration between:
1. High-throughput REST and Server-Sent Event (SSE) streaming APIs.
2. Low-latency relational data management (customers, accounts, payments, transactions, audit trails).
3. Machine learning anomaly detection and multi-class incident classification (Scikit-Learn, XGBoost, SHAP).
4. Retrieval-Augmented Generation (RAG) vector embeddings and semantic search (Qdrant, Ollama).
5. Autonomous multi-agent coordination with tool execution.

Building the banking microservices in Java/Spring Boot and the AI agents in Python would introduce cross-process serialization overhead, multiple runtime environments, and dual-language maintenance complexity for single-developer or small SRE teams.

## Decision
We adopted **Python 3.11+ with FastAPI, SQLAlchemy 2.0 (asyncio), and Pydantic v2** as the unified platform language and framework across all banking microservices, AI agents, simulation generators, and API layers.

## Consequences
### Positive
- **Zero Serialization Boundary**: Microservice state, telemetry metrics, and ML feature extractors share memory and data structures directly without gRPC/REST hops during investigation.
- **Native AI/ML Ecosystem**: Native execution of Scikit-learn, XGBoost, and vector stores without IPC bridges.
- **Asynchronous Concurrency**: FastAPI's async runtime natively handles real-time SSE progress streams to the frontend command center while executing asynchronous agent tool queries.
- **Rapid Local Development**: Zero-dependency SQLite and in-memory Qdrant allow instant local testing without spinning up 6 heavy Docker containers.

### Negative
- Python GIL limits single-process CPU parallelism for heavy simulation generation (mitigated by asynchronous I/O and process pool workers for ML inference when necessary).
