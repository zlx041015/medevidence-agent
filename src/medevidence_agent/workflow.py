from rich.console import Console
from typing import Callable

from medevidence_agent.config import Settings
from medevidence_agent.models import ClinicalQuestion, WorkflowState
from medevidence_agent.nodes.extractor import extract_evidence
from medevidence_agent.nodes.planner import build_search_plan
from medevidence_agent.nodes.verifier import verify_evidence
from medevidence_agent.nodes.writer import write_answer
from medevidence_agent.tools.pubmed import fetch_pubmed_articles, search_pubmed_pmids
from medevidence_agent.tools.search import keyword_overlap_score
from medevidence_agent.tools.search import retrieve_sources
from medevidence_agent.tools.storage import load_mock_sources


console = Console()


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
        query = " ".join(state.plan.keywords)
        pmids = search_pubmed_pmids(query, retmax=max(settings.top_k, 5))
        sources = fetch_pubmed_articles(pmids)
        for source in sources:
            overlap = keyword_overlap_score(state.plan.keywords, source.content)
            final_score = 0.6 * overlap + 0.4 * source.quality_score
            source.relevance_score = round(final_score, 3)
        sources.sort(key=lambda item: item.relevance_score, reverse=True)
        state.candidate_sources = sources[: settings.top_k]
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
