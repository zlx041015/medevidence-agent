from dataclasses import dataclass

from medevidence_agent.models import SearchPlan, SourceDocument
from medevidence_agent.rag.retriever import build_rag_context, persist_documents_to_store
from medevidence_agent.tools.pubmed import fetch_pubmed_articles, search_pubmed_pmids_with_fallback
from medevidence_agent.tools.search import keyword_overlap_score, retrieve_sources, split_disease_and_support_terms
from medevidence_agent.tools.storage import load_mock_sources


@dataclass
class RetrievalBundle:
    sources: list[SourceDocument]
    retrieval_mode: str


def apply_source_scoring(
    documents: list[SourceDocument],
    query_terms: list[str],
    use_source_type_weighting: bool = True,
) -> list[SourceDocument]:
    type_weights = {
        "guideline": 0.12,
        "systematic_review": 0.10,
        "meta_analysis": 0.10,
        "review": 0.06,
        "trial": 0.06,
        "pubmed_article": 0.04,
        "consensus": 0.08,
        "knowledge_base": 0.05,
        "case_report": 0.02,
        "blog": -0.08,
    }

    disease_terms, support_terms = split_disease_and_support_terms(query_terms)

    for source in documents:
        disease_overlap = keyword_overlap_score(disease_terms, source.content) if disease_terms else 0.0
        support_overlap = keyword_overlap_score(support_terms, source.content) if support_terms else 0.0
        overlap = 0.75 * disease_overlap + 0.25 * support_overlap
        score = 0.6 * overlap + 0.4 * source.quality_score
        if use_source_type_weighting:
            score += type_weights.get(source.source_type, 0.0)
        if disease_terms and disease_overlap == 0:
            score -= 0.18
        source.relevance_score = round(max(0.0, min(score, 1.0)), 3)

    documents.sort(key=lambda item: item.relevance_score, reverse=True)
    return documents


def compress_rag_chunks_to_sources(chunks) -> list[SourceDocument]:
    grouped: dict[str, SourceDocument] = {}
    order: list[str] = []

    for chunk in chunks:
        existing = grouped.get(chunk.source_id)
        if existing is None:
            grouped[chunk.source_id] = SourceDocument(
                source_id=chunk.source_id,
                title=chunk.title,
                source_type=chunk.source_type,
                year=chunk.year,
                url=chunk.url,
                quality_score=0.78,
                content=chunk.text,
                relevance_score=chunk.score,
            )
            order.append(chunk.source_id)
        else:
            existing.content += f"\n\n{chunk.text}"
            existing.relevance_score = max(existing.relevance_score, chunk.score)

    return [grouped[source_id] for source_id in order]


def load_mock_documents(path) -> list[SourceDocument]:
    return load_mock_sources(path)


def retrieve_documents(
    plan: SearchPlan,
    settings,
    source_mode: str,
    use_rag: bool = True,
    use_source_type_weighting: bool = True,
) -> RetrievalBundle:
    if source_mode == "pubmed":
        pmids = search_pubmed_pmids_with_fallback(
            plan.keywords,
            retmax=max(settings.top_k, 8),
        )
        raw_sources = fetch_pubmed_articles(pmids)
        scored_sources = apply_source_scoring(
            raw_sources,
            plan.keywords,
            use_source_type_weighting=use_source_type_weighting,
        )
        if use_rag:
            persist_documents_to_store(scored_sources, settings.rag_store_path)
            rag_chunks = build_rag_context(
                scored_sources,
                plan.keywords,
                top_k_chunks=settings.rag_top_k_chunks,
                sparse_weight=settings.rag_sparse_weight,
                dense_weight=settings.rag_dense_weight,
            )
            return RetrievalBundle(
                sources=compress_rag_chunks_to_sources(rag_chunks)[: settings.top_k],
                retrieval_mode="pubmed_rag",
            )

        return RetrievalBundle(
            sources=scored_sources[: settings.top_k],
            retrieval_mode="pubmed_ranked",
        )

    sources = load_mock_documents(settings.data_path)
    if source_mode == "hybrid_mock":
        sources.extend(load_mock_sources(settings.data_path.parent / "guideline_sources.json"))
        sources = apply_source_scoring(
            sources,
            plan.keywords,
            use_source_type_weighting=use_source_type_weighting,
        )
        if use_rag:
            rag_chunks = build_rag_context(
                sources,
                plan.keywords,
                top_k_chunks=settings.rag_top_k_chunks,
                sparse_weight=settings.rag_sparse_weight,
                dense_weight=settings.rag_dense_weight,
            )
            filtered = compress_rag_chunks_to_sources(rag_chunks)[: settings.top_k]
        else:
            filtered = sources[: settings.top_k]
        return RetrievalBundle(sources=filtered, retrieval_mode="hybrid_mock")

    filtered = retrieve_sources(
        plan=plan,
        sources=sources,
        top_k=settings.top_k,
        evidence_score_threshold=settings.evidence_score_threshold,
    )
    if use_source_type_weighting:
        filtered = apply_source_scoring(filtered, plan.keywords, use_source_type_weighting=True)
    return RetrievalBundle(sources=filtered[: settings.top_k], retrieval_mode="mock")
