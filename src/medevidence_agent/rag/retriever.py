from medevidence_agent.models import SourceDocument
from medevidence_agent.rag.chunker import RagChunk, chunk_documents
from medevidence_agent.rag.embedder import cosine_similarity, embed_text
from medevidence_agent.rag.store import StoredChunk, load_rag_store, merge_chunks, save_rag_store
from medevidence_agent.tools.search import keyword_overlap_score


def score_chunks(query_terms: list[str], chunks: list[RagChunk]) -> list[RagChunk]:
    rescored: list[RagChunk] = []
    for chunk in chunks:
        overlap = keyword_overlap_score(query_terms, chunk.text)
        chunk.score = round(overlap, 3)
        rescored.append(chunk)
    rescored.sort(key=lambda item: item.score, reverse=True)
    return rescored


def build_dense_store(documents: list[SourceDocument]) -> list[StoredChunk]:
    stored: list[StoredChunk] = []
    for chunk in chunk_documents(documents):
        stored.append(
            StoredChunk(
                chunk_id=chunk.chunk_id,
                source_id=chunk.source_id,
                title=chunk.title,
                source_type=chunk.source_type,
                year=chunk.year,
                url=chunk.url,
                text=chunk.text,
                embedding=embed_text(chunk.text),
            )
        )
    return stored


def persist_documents_to_store(documents: list[SourceDocument], path) -> None:
    existing = load_rag_store(path)
    new_chunks = build_dense_store(documents)
    merged = merge_chunks(existing, new_chunks)
    save_rag_store(path, merged)


def score_chunks_hybrid(
    query_terms: list[str],
    chunks: list[RagChunk],
    sparse_weight: float = 0.5,
    dense_weight: float = 0.5,
) -> list[RagChunk]:
    query_text = " ".join(query_terms)
    query_embedding = embed_text(query_text)

    rescored: list[RagChunk] = []
    for chunk in chunks:
        sparse_score = keyword_overlap_score(query_terms, chunk.text)
        dense_score = max(0.0, cosine_similarity(query_embedding, embed_text(chunk.text)))
        chunk.score = round(sparse_weight * sparse_score + dense_weight * dense_score, 3)
        rescored.append(chunk)

    rescored.sort(key=lambda item: item.score, reverse=True)
    return rescored


def build_rag_context(
    documents: list[SourceDocument],
    query_terms: list[str],
    top_k_chunks: int = 6,
    sparse_weight: float = 0.5,
    dense_weight: float = 0.5,
) -> list[RagChunk]:
    chunks = chunk_documents(documents)
    scored = score_chunks_hybrid(
        query_terms,
        chunks,
        sparse_weight=sparse_weight,
        dense_weight=dense_weight,
    )
    return scored[:top_k_chunks]
