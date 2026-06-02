from dataclasses import dataclass

from medevidence_agent.models import SourceDocument


@dataclass(slots=True)
class RagChunk:
    chunk_id: str
    source_id: str
    title: str
    source_type: str
    year: int
    url: str
    text: str
    score: float = 0.0


def chunk_source_document(source: SourceDocument) -> list[RagChunk]:
    parts = [part.strip() for part in source.content.split("\n\n") if part.strip()]
    if not parts:
        parts = [source.title]

    chunks: list[RagChunk] = []
    for idx, text in enumerate(parts, start=1):
        chunks.append(
            RagChunk(
                chunk_id=f"{source.source_id}_chunk_{idx}",
                source_id=source.source_id,
                title=source.title,
                source_type=source.source_type,
                year=source.year,
                url=source.url,
                text=text,
            )
        )
    return chunks


def chunk_documents(documents: list[SourceDocument]) -> list[RagChunk]:
    chunks: list[RagChunk] = []
    for document in documents:
        chunks.extend(chunk_source_document(document))
    return chunks
