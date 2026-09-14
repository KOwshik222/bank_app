"""
Ingest pipeline — crawls knowledge_base directory, extracts markdown chunks,
and indexes them into the Qdrant vector store.
"""

import logging
from pathlib import Path
from typing import Any

from ai.rag.chunker import chunk_markdown_file
from ai.rag.retriever import get_vector_store
from ai.rag.vector_store import VectorStore

logger = logging.getLogger(__name__)


def ingest_knowledge_base(kb_dir: Path | None = None, store: VectorStore | None = None) -> dict[str, Any]:
    """Ingest all markdown documents from knowledge_base directory into Qdrant."""
    if kb_dir is None:
        kb_dir = Path(__file__).resolve().parent.parent.parent / "knowledge_base"

    if store is None:
        store = get_vector_store()

    if not kb_dir.exists():
        raise FileNotFoundError(f"Knowledge base directory not found at {kb_dir}")

    total_files = 0
    total_chunks = 0
    all_chunks = []
    category_counts = {}

    for md_file in kb_dir.glob("**/*.md"):
        total_files += 1
        category = md_file.parent.name
        chunks = chunk_markdown_file(md_file)
        category_counts[category] = category_counts.get(category, 0) + len(chunks)

        for c in chunks:
            all_chunks.append(c.to_dict())

    total_chunks = len(all_chunks)
    logger.info(f"Chunked {total_files} files into {total_chunks} passages.")

    upserted = store.upsert_chunks(all_chunks)

    summary = {
        "status": "SUCCESS",
        "total_files": total_files,
        "total_chunks": total_chunks,
        "upserted_vectors": upserted,
        "categories": category_counts,
    }
    return summary


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("Starting Knowledge Base Ingestion...")
    summary = ingest_knowledge_base()
    print("Ingestion Summary:")
    print(f"Files: {summary['total_files']}")
    print(f"Total Chunks: {summary['total_chunks']}")
    print(f"Vector Count: {summary['upserted_vectors']}")
    for cat, cnt in summary["categories"].items():
        print(f"  - {cat}: {cnt} chunks")
