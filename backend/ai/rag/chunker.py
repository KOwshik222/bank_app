"""
Document Chunker — splits markdown documents into semantic chunks with metadata.
Preserves headers, sections, and document attribution for RAG.
"""

import re
from pathlib import Path
from typing import Any


class DocumentChunk:
    """Represents a chunk of a knowledge base document with metadata."""

    def __init__(
        self,
        content: str,
        source_file: str,
        category: str,
        title: str,
        section: str = "",
        chunk_index: int = 0,
    ):
        self.content = content.strip()
        self.source_file = source_file
        self.category = category
        self.title = title
        self.section = section
        self.chunk_index = chunk_index

    def to_dict(self) -> dict[str, Any]:
        return {
            "content": self.content,
            "source_file": self.source_file,
            "category": self.category,
            "title": self.title,
            "section": self.section,
            "chunk_index": self.chunk_index,
        }


def chunk_markdown_file(file_path: Path, max_chars: int = 800, overlap: int = 100) -> list[DocumentChunk]:
    """
    Splits a markdown document into semantic section chunks.
    Extracts title (# Title) and section headers (## Section).
    """
    text = file_path.read_text(encoding="utf-8")
    category = file_path.parent.name
    filename = file_path.name

    # Extract document title
    title_match = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
    title = title_match.group(1).strip() if title_match else filename

    # Split by section headers (## or ###)
    sections = re.split(r"(^#{2,3}\s+.+$)", text, flags=re.MULTILINE)

    chunks: list[DocumentChunk] = []
    current_section = "Overview"
    current_text = ""
    chunk_idx = 0

    if len(sections) == 1:
        # No subsections, chunk by paragraph
        paragraphs = text.split("\n\n")
        buf = ""
        for p in paragraphs:
            if len(buf) + len(p) < max_chars:
                buf += "\n\n" + p if buf else p
            else:
                if buf:
                    chunks.append(DocumentChunk(buf, filename, category, title, "General", chunk_idx))
                    chunk_idx += 1
                buf = p
        if buf:
            chunks.append(DocumentChunk(buf, filename, category, title, "General", chunk_idx))
        return chunks

    i = 0
    while i < len(sections):
        part = sections[i].strip()
        if not part:
            i += 1
            continue

        if re.match(r"^#{2,3}\s+", part):
            current_section = re.sub(r"^#{2,3}\s+", "", part).strip()
            if i + 1 < len(sections):
                content = sections[i + 1].strip()
                if content:
                    full_chunk = f"## {current_section}\n{content}"
                    chunks.append(DocumentChunk(full_chunk, filename, category, title, current_section, chunk_idx))
                    chunk_idx += 1
                i += 2
            else:
                i += 1
        else:
            if part:
                chunks.append(DocumentChunk(part, filename, category, title, "Introduction", chunk_idx))
                chunk_idx += 1
            i += 1

    return chunks
