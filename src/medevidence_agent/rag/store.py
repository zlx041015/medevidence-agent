import json
from dataclasses import asdict, dataclass
from pathlib import Path

from medevidence_agent.rag.chunker import RagChunk


@dataclass(slots=True)
class StoredChunk:
    chunk_id: str
    source_id: str
    title: str
    source_type: str
    year: int
    url: str
    text: str
    embedding: list[float]


def load_rag_store(path: Path) -> list[StoredChunk]:
    if not path.exists():
        return []
    raw = json.loads(path.read_text(encoding="utf-8"))
    return [StoredChunk(**item) for item in raw]


def save_rag_store(path: Path, chunks: list[StoredChunk]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps([asdict(chunk) for chunk in chunks], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def merge_chunks(existing: list[StoredChunk], new_chunks: list[StoredChunk]) -> list[StoredChunk]:
    merged = {chunk.chunk_id: chunk for chunk in existing}
    for chunk in new_chunks:
        merged[chunk.chunk_id] = chunk
    return list(merged.values())


def rag_chunks_from_stored(chunks: list[StoredChunk]) -> list[RagChunk]:
    return [
        RagChunk(
            chunk_id=chunk.chunk_id,
            source_id=chunk.source_id,
            title=chunk.title,
            source_type=chunk.source_type,
            year=chunk.year,
            url=chunk.url,
            text=chunk.text,
            score=0.0,
        )
        for chunk in chunks
    ]
