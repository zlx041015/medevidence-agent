from rich.console import Console

from medevidence_agent.config import Settings
from medevidence_agent.models import ClinicalQuestion, WorkflowState
from medevidence_agent.nodes.extractor import extract_evidence
from medevidence_agent.nodes.planner import build_search_plan
from medevidence_agent.nodes.verifier import verify_evidence
from medevidence_agent.nodes.writer import write_answer
from medevidence_agent.tools.search import retrieve_sources
from medevidence_agent.tools.storage import load_mock_sources


console = Console()


def run_workflow(question_text: str, settings: Settings) -> WorkflowState:
    state = WorkflowState(question=ClinicalQuestion(text=question_text))

    console.rule("Planner")
    state.plan = build_search_plan(state.question, settings)
    console.print(
        {
            "intent": state.plan.intent,
            "keywords": state.plan.keywords,
            "risk_level": state.plan.risk_level,
        }
    )

    console.rule("Retriever")
    sources = load_mock_sources(settings.data_path)
    state.candidate_sources = retrieve_sources(
        plan=state.plan,
        sources=sources,
        top_k=settings.top_k,
        evidence_score_threshold=settings.evidence_score_threshold,
    )
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

    console.rule("Extractor")
    state.evidence_items = extract_evidence(state.candidate_sources, settings)
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

    console.rule("Verifier")
    state.verification = verify_evidence(
        evidence_items=state.evidence_items,
        confidence_threshold=settings.confidence_threshold,
    )
    console.print(
        {
            "summary_claim": state.verification.summary_claim,
            "confidence": state.verification.confidence,
            "needs_human_review": state.verification.needs_human_review,
            "conflicts": state.verification.conflicts,
        }
    )

    console.rule("Writer")
    state.final_answer = write_answer(state.verification, settings)
    console.print(state.final_answer.answer)
    console.print(state.final_answer.references)

    return state