from typing import Callable, Optional

try:
    from rich.console import Console
except ImportError:
    class Console:
        def rule(self, title: str) -> None:
            print(f"== {title} ==")

        def print(self, payload) -> None:
            print(payload)

from medevidence_agent.agents import MultiAgentCoordinator
from medevidence_agent.config import Settings
from medevidence_agent.models import ClinicalQuestion, WorkflowOptions, WorkflowState


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

    coordinator = MultiAgentCoordinator()

    update_progress("开始多智能体工作流", 0, 5)
    state = coordinator.run(state, settings, options)

    if verbose:
        console.rule("多智能体执行轨迹")
        console.print(
            [
                {
                    "agent": record.agent_name,
                    "status": record.status,
                    "notes": record.notes,
                }
                for record in state.agent_trace
            ]
        )

        if state.plan:
            console.rule("Planner Agent")
            console.print(
                {
                    "intent": state.plan.intent,
                    "keywords": state.plan.keywords,
                    "risk_level": state.plan.risk_level,
                }
            )

        if state.candidate_sources:
            console.rule("Retriever Agent")
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

        if state.evidence_items:
            console.rule("Extractor Agent")
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

        if state.verification:
            console.rule("Verifier Agent")
            console.print(
                {
                    "summary_claim": state.verification.summary_claim,
                    "confidence": state.verification.confidence,
                    "needs_human_review": state.verification.needs_human_review,
                    "conflicts": state.verification.conflicts,
                    "checks": state.verification.check_results,
                }
            )

        if state.final_answer:
            console.rule("Writer Agent")
            console.print(state.final_answer.answer)
            console.print(state.final_answer.references)

    update_progress("多智能体工作流完成", 5, 5)
    return state
