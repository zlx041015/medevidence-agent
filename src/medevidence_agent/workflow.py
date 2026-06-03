from typing import Callable, Optional

try:
    from rich.console import Console
except ImportError:
    class Console:
        def rule(self, title: str) -> None:
            print(f"== {title} ==")

        def print(self, payload) -> None:
            print(payload)

from medevidence_agent.config import Settings
from medevidence_agent.models import ClinicalQuestion, VerificationResult, WorkflowOptions, WorkflowState
from medevidence_agent.nodes.extractor import extract_evidence_with_mode
from medevidence_agent.nodes.planner import build_rule_based_search_plan, build_search_plan
from medevidence_agent.nodes.verifier import verify_evidence
from medevidence_agent.nodes.writer import write_answer, write_answer_rule_based
from medevidence_agent.retrieval import retrieve_documents


console = Console()


def run_workflow(
    question_text: str,
    settings: Settings,
    verbose: bool = True,
    progress_callback: Optional[Callable[[str, int, int], None]] = None,
    options: Optional[WorkflowOptions] = None,
) -> WorkflowState:
    options = options or WorkflowOptions()
    state = WorkflowState(question=ClinicalQuestion(text=question_text))

    def update_progress(stage: str, current: int, total: int) -> None:
        if progress_callback is not None:
            progress_callback(stage, current, total)

    update_progress("开始分析", 0, 5)

    if verbose:
        console.rule("规划节点")
    update_progress("生成检索计划", 1, 5)
    if options.use_planner:
        state.plan = build_search_plan(state.question, settings)
    else:
        state.plan = build_rule_based_search_plan(state.question)
    if verbose:
        console.print(
            {
                "intent": state.plan.intent,
                "keywords": state.plan.keywords,
                "risk_level": state.plan.risk_level,
            }
        )

    if verbose:
        console.rule("检索节点")
    update_progress("检索候选来源", 2, 5)
    retrieval = retrieve_documents(
        plan=state.plan,
        settings=settings,
        source_mode=options.source_mode_override or settings.source_mode,
        use_rag=options.use_rag,
        use_source_type_weighting=options.use_source_type_weighting,
    )
    state.candidate_sources = retrieval.sources
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
        console.rule("抽取节点")
    update_progress("抽取结构化证据", 3, 5)
    state.evidence_items = extract_evidence_with_mode(
        state.candidate_sources,
        settings,
        mode=options.extractor_mode,
    )
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
        console.rule("核验节点")
    update_progress("核验证据", 4, 5)
    if options.use_verifier:
        state.verification = verify_evidence(
            question_text=state.question.text,
            evidence_items=state.evidence_items,
            confidence_threshold=settings.confidence_threshold,
        )
    else:
        avg_score = (
            sum(item.score for item in state.evidence_items) / len(state.evidence_items)
            if state.evidence_items
            else 0.0
        )
        state.verification = VerificationResult(
            summary_claim="本次消融实验跳过了 verifier 核验阶段。",
            confidence=round(avg_score, 3),
            supporting_evidence=state.evidence_items,
            check_results={"verifier": "已关闭"},
            evidence_coverage=1.0 if state.evidence_items else 0.0,
            needs_human_review=False,
        )
    if verbose:
        console.print(
            {
                "summary_claim": state.verification.summary_claim,
                "confidence": state.verification.confidence,
                "needs_human_review": state.verification.needs_human_review,
                "conflicts": state.verification.conflicts,
                "checks": state.verification.check_results,
            }
        )

    if verbose:
        console.rule("生成节点")
    update_progress("生成最终回答", 5, 5)
    if options.use_verifier:
        state.final_answer = write_answer(state.question.text, state.verification, settings)
    else:
        state.final_answer = write_answer_rule_based(state.question.text, state.verification)
    if verbose:
        console.print(state.final_answer.answer)
        console.print(state.final_answer.references)

    return state
