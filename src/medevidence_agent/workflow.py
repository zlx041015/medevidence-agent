from collections import OrderedDict
from typing import Callable

from rich.console import Console

from medevidence_agent.config import Settings
from medevidence_agent.models import ClinicalQuestion, SourceDocument, WorkflowState
from medevidence_agent.nodes.extractor import extract_evidence
from medevidence_agent.nodes.planner import build_search_plan
from medevidence_agent.nodes.verifier import verify_evidence
from medevidence_agent.nodes.writer import write_answer
from medevidence_agent.rag.retriever import build_rag_context, persist_documents_to_store
from medevidence_agent.tools.pubmed import (
    fetch_pubmed_articles,
    search_pubmed_pmids_with_fallback,
)
from medevidence_agent.tools.search import keyword_overlap_score, retrieve_sources
from medevidence_agent.tools.storage import load_mock_sources


console = Console()


def _apply_pubmed_scoring(documents: list[SourceDocument], query_terms: list[str]) -> list[SourceDocument]:
    for source in documents:
        overlap = keyword_overlap_score(query_terms, source.content)
        final_score = 0.6 * overlap + 0.4 * source.quality_score
        source.relevance_score = round(final_score, 3)
    documents.sort(key=lambda item: item.relevance_score, reverse=True)
    return documents


def _compress_rag_chunks_to_sources(chunks) -> list[SourceDocument]:
    grouped: OrderedDict[str, SourceDocument] = OrderedDict()

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
        else:
            existing.content += f"\n\n{chunk.text}"
            existing.relevance_score = max(existing.relevance_score, chunk.score)

    return list(grouped.values())


def run_workflow(
    question_text: str,
    settings: Settings,
    verbose: bool = True,
    progress_callback: Callable[[str, int, int], None] | None = None,
) -> WorkflowState:
    state = WorkflowState(question=ClinicalQuestion(text=question_text))

    def update_progress(stage: str, current: int, total: int) -> None:
        if progress_callback is not None:
            progress_callback(stage, current, total)

    update_progress("开始分析", 0, 5)

    if verbose:
        console.rule("Planner")
    update_progress("规划检索问题", 1, 5)
    state.plan = build_search_plan(state.question, settings)
    if verbose:
        console.print(
            {
                "intent": state.plan.intent,
                "keywords": state.plan.keywords,
                "risk_level": state.plan.risk_level,
            }
        )

    if verbose:
        console.rule("Retriever")
    update_progress("检索候选来源", 2, 5)

    if settings.source_mode == "pubmed":
        pmids = search_pubmed_pmids_with_fallback(
            state.plan.keywords,
            retmax=max(settings.top_k, 8),
        )
        raw_sources = fetch_pubmed_articles(pmids)
        scored_sources = _apply_pubmed_scoring(raw_sources, state.plan.keywords)
        persist_documents_to_store(scored_sources, settings.rag_store_path)
        rag_chunks = build_rag_context(
            scored_sources,
            state.plan.keywords,
            top_k_chunks=settings.rag_top_k_chunks,
            sparse_weight=settings.rag_sparse_weight,
            dense_weight=settings.rag_dense_weight,
        )
        state.candidate_sources = _compress_rag_chunks_to_sources(rag_chunks)[: settings.top_k]
    else:
        sources = load_mock_sources(settings.data_path)
        state.candidate_sources = retrieve_sources(
            plan=state.plan,
            sources=sources,
            top_k=settings.top_k,
            evidence_score_threshold=settings.evidence_score_threshold,
        )

    if verbose:
        console.print(
            [
                {
                    "title": source.title,
                    "score": source.relevance_score,
                    "year": source.year,
                    "type": source.source_type,
                }
                for source in state.candidate_sources
            ]
        )

    if verbose:
        console.rule("Extractor")
    update_progress("抽取证据信息", 3, 5)
    state.evidence_items = extract_evidence(state.candidate_sources, settings)
    if verbose:
        console.print(
            [
                {
                    "title": item.title,
                    "score": item.score,
                    "claim": item.claim,
                }
                for item in state.evidence_items
            ]
        )

    if verbose:
        console.rule("Verifier")
    update_progress("审核与评估证据", 4, 5)
    state.verification = verify_evidence(
        question_text=state.question.text,
        evidence_items=state.evidence_items,
        confidence_threshold=settings.confidence_threshold,
    )
    if verbose:
        console.print(
            {
                "summary_claim": state.verification.summary_claim,
                "confidence": state.verification.confidence,
                "needs_human_review": state.verification.needs_human_review,
                "conflicts": state.verification.conflicts,
            }
        )

    if verbose:
        console.rule("Writer")
    update_progress("生成最终总结", 5, 5)
    state.final_answer = write_answer(state.verification, settings)
    if verbose:
        console.print(state.final_answer.answer)
        console.print(state.final_answer.references)

    return state
