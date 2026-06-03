from dataclasses import dataclass
from typing import Optional

from medevidence_agent.config import Settings
from medevidence_agent.models import BenchmarkQuestion, MethodRunResult, VerificationResult, WorkflowOptions
from medevidence_agent.nodes.planner import build_rule_based_search_plan
from medevidence_agent.nodes.verifier import verify_evidence
from medevidence_agent.nodes.writer import write_answer_rule_based
from medevidence_agent.retrieval import retrieve_documents
from medevidence_agent.workflow import run_workflow


@dataclass
class MethodDefinition:
    name: str
    description: str
    options: Optional[WorkflowOptions] = None
    special_runner: Optional[str] = None


def _state_to_result(method_name: str, benchmark: BenchmarkQuestion, state) -> MethodRunResult:
    return MethodRunResult(
        method_name=method_name,
        question_id=benchmark.question_id,
        question=benchmark.question,
        answer=state.final_answer.answer if state.final_answer else "",
        references=state.final_answer.references if state.final_answer else [],
        retrieved_source_ids=[source.source_id for source in state.candidate_sources],
        extracted_claims=[item.claim for item in state.evidence_items],
        summary_claim=state.verification.summary_claim if state.verification else "",
        confidence=state.verification.confidence if state.verification else 0.0,
        needs_human_review=state.verification.needs_human_review if state.verification else False,
        conflicts=state.verification.conflicts if state.verification else [],
        check_results=state.verification.check_results if state.verification else {},
    )


def run_direct_llm_baseline(benchmark: BenchmarkQuestion, settings: Settings) -> MethodRunResult:
    fallback_answer = (
        "Direct LLM baseline unavailable in offline mode. This placeholder intentionally has no retrieval evidence."
    )
    return MethodRunResult(
        method_name="direct_llm",
        question_id=benchmark.question_id,
        question=benchmark.question,
        answer=fallback_answer,
        references=[],
        retrieved_source_ids=[],
        extracted_claims=[],
        summary_claim="No evidence-backed summary was produced in offline baseline mode.",
        confidence=0.2,
        needs_human_review=True,
        conflicts=["Direct LLM baseline was simulated offline without source grounding."],
        check_results={"baseline_mode": "offline_placeholder"},
        failure_reason="offline_llm_unavailable",
    )


def run_retrieve_then_summarize(benchmark: BenchmarkQuestion, settings: Settings) -> MethodRunResult:
    plan = build_rule_based_search_plan(type("Question", (), {"text": benchmark.question})())
    retrieval = retrieve_documents(
        plan=plan,
        settings=settings,
        source_mode="hybrid_mock",
        use_rag=False,
        use_source_type_weighting=True,
    )
    evidence_items = []
    for source in retrieval.sources:
        evidence_items.append(
            type(
                "EvidenceItemProxy",
                (),
                {
                    "source_id": source.source_id,
                    "title": source.title,
                    "claim": source.content.split(".")[0].strip(),
                    "support_text": source.content,
                    "source_type": source.source_type,
                    "year": source.year,
                    "url": source.url,
                    "score": source.relevance_score,
                },
            )()
        )
    verification = verify_evidence(benchmark.question, evidence_items, settings.confidence_threshold)
    final_answer = write_answer_rule_based(benchmark.question, verification)
    state = type(
        "SimpleState",
        (),
        {
            "candidate_sources": retrieval.sources,
            "evidence_items": evidence_items,
            "verification": verification,
            "final_answer": final_answer,
        },
    )()
    return _state_to_result("retrieve_then_summarize", benchmark, state)


def build_method_definitions() -> list[MethodDefinition]:
    return [
        MethodDefinition(
            name="direct_llm",
            description="Offline placeholder baseline for direct answer generation.",
            special_runner="direct_llm",
        ),
        MethodDefinition(
            name="retrieve_then_summarize",
            description="Retrieval plus heuristic summarization without workflow decomposition.",
            special_runner="retrieve_then_summarize",
        ),
        MethodDefinition(
            name="current_workflow",
            description="Current workflow using planner, retrieval, extractor, verifier, and writer.",
            options=WorkflowOptions(
                use_planner=True,
                use_verifier=True,
                use_rag=False,
                use_source_type_weighting=False,
                extractor_mode="auto",
                source_mode_override="mock",
            ),
        ),
        MethodDefinition(
            name="workflow_with_rag_and_verifier",
            description="Upgraded workflow using hybrid retrieval, RAG, source weighting, and enhanced verifier.",
            options=WorkflowOptions(
                use_planner=True,
                use_verifier=True,
                use_rag=True,
                use_source_type_weighting=True,
                extractor_mode="auto",
                source_mode_override="hybrid_mock",
            ),
        ),
    ]


def run_method(definition: MethodDefinition, benchmark: BenchmarkQuestion, settings: Settings) -> MethodRunResult:
    if definition.special_runner == "direct_llm":
        return run_direct_llm_baseline(benchmark, settings)
    if definition.special_runner == "retrieve_then_summarize":
        return run_retrieve_then_summarize(benchmark, settings)

    state = run_workflow(
        benchmark.question,
        settings,
        verbose=False,
        options=definition.options,
    )
    return _state_to_result(definition.name, benchmark, state)
