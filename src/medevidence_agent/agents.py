from dataclasses import dataclass
from typing import Callable, Optional

from medevidence_agent.config import Settings
from medevidence_agent.models import (
    AgentRunRecord,
    ClinicalQuestion,
    FinalAnswer,
    VerificationResult,
    WorkflowOptions,
    WorkflowState,
)
from medevidence_agent.nodes.extractor import extract_evidence_with_mode
from medevidence_agent.nodes.planner import build_rule_based_search_plan, build_search_plan
from medevidence_agent.nodes.verifier import verify_evidence
from medevidence_agent.nodes.writer import write_answer, write_answer_rule_based
from medevidence_agent.retrieval import retrieve_documents


@dataclass
class AgentResult:
    next_agent: Optional[str] = None
    notes: str = ""


class BaseAgent:
    name = "base_agent"

    def run(self, state: WorkflowState, settings: Settings, options: WorkflowOptions) -> AgentResult:
        raise NotImplementedError

    def _record(self, state: WorkflowState, status: str, notes: str = "") -> None:
        state.agent_trace.append(
            AgentRunRecord(
                agent_name=self.name,
                status=status,
                notes=notes,
            )
        )


class PlannerAgent(BaseAgent):
    name = "planner_agent"

    def run(self, state: WorkflowState, settings: Settings, options: WorkflowOptions) -> AgentResult:
        if options.use_planner:
            state.plan = build_search_plan(state.question, settings)
            self._record(state, "completed", "Search plan generated.")
        else:
            state.plan = build_rule_based_search_plan(state.question)
            self._record(state, "completed", "Rule-based planner used.")
        return AgentResult(next_agent="retriever_agent", notes="Planner completed.")


class RetrieverAgent(BaseAgent):
    name = "retriever_agent"

    def run(self, state: WorkflowState, settings: Settings, options: WorkflowOptions) -> AgentResult:
        retrieval = retrieve_documents(
            plan=state.plan,
            settings=settings,
            source_mode=options.source_mode_override or settings.source_mode,
            use_rag=options.use_rag,
            use_source_type_weighting=options.use_source_type_weighting,
        )
        state.candidate_sources = retrieval.sources
        self._record(state, "completed", f"Retrieved {len(state.candidate_sources)} sources.")
        return AgentResult(next_agent="extractor_agent", notes="Retriever completed.")


class ExtractorAgent(BaseAgent):
    name = "extractor_agent"

    def run(self, state: WorkflowState, settings: Settings, options: WorkflowOptions) -> AgentResult:
        state.evidence_items = extract_evidence_with_mode(
            state.candidate_sources,
            settings,
            mode=options.extractor_mode,
        )
        self._record(state, "completed", f"Extracted {len(state.evidence_items)} evidence items.")
        return AgentResult(next_agent="verifier_agent", notes="Extractor completed.")


class VerifierAgent(BaseAgent):
    name = "verifier_agent"

    def run(self, state: WorkflowState, settings: Settings, options: WorkflowOptions) -> AgentResult:
        if options.use_verifier:
            state.verification = verify_evidence(
                question_text=state.question.text,
                evidence_items=state.evidence_items,
                confidence_threshold=settings.confidence_threshold,
                mesh_terms=state.plan.mesh_terms if state.plan else [],
            )
            self._record(state, "completed", "Verifier completed.")
        else:
            avg_score = (
                sum(item.score for item in state.evidence_items) / len(state.evidence_items)
                if state.evidence_items
                else 0.0
            )
            state.verification = VerificationResult(
                summary_claim="Verification bypassed for this ablation run.",
                confidence=round(avg_score, 3),
                supporting_evidence=state.evidence_items,
                check_results={"verifier": "disabled"},
                evidence_coverage=1.0 if state.evidence_items else 0.0,
                needs_human_review=False,
            )
            self._record(state, "completed", "Verifier bypassed.")
        return AgentResult(next_agent="writer_agent", notes="Verifier completed.")


class WriterAgent(BaseAgent):
    name = "writer_agent"

    def run(self, state: WorkflowState, settings: Settings, options: WorkflowOptions) -> AgentResult:
        if options.use_verifier:
            state.final_answer = write_answer(state.question.text, state.verification, settings)
            self._record(state, "completed", "Writer completed with verifier.")
        else:
            state.final_answer = write_answer_rule_based(state.question.text, state.verification)
            self._record(state, "completed", "Writer completed without verifier.")
        return AgentResult(next_agent=None, notes="Workflow finished.")


class MultiAgentCoordinator:
    def __init__(self) -> None:
        self.agents = {
            "planner_agent": PlannerAgent(),
            "retriever_agent": RetrieverAgent(),
            "extractor_agent": ExtractorAgent(),
            "verifier_agent": VerifierAgent(),
            "writer_agent": WriterAgent(),
        }

    def run(
        self,
        state: WorkflowState,
        settings: Settings,
        options: WorkflowOptions,
        start_agent: str = "planner_agent",
        progress_callback: Optional[Callable[[str, int, int], None]] = None,
    ) -> WorkflowState:
        current_agent = start_agent
        seen = {}
        step_count = 0
        ordered_agents = [
            "planner_agent",
            "retriever_agent",
            "extractor_agent",
            "verifier_agent",
            "writer_agent",
        ]
        total_steps = len(ordered_agents)
        stage_names = {
            "planner_agent": "规划阶段",
            "retriever_agent": "检索阶段",
            "extractor_agent": "抽取阶段",
            "verifier_agent": "核验阶段",
            "writer_agent": "生成阶段",
        }

        while current_agent is not None:
            step_count += 1
            if step_count > options.max_agent_steps:
                state.agent_trace.append(
                    AgentRunRecord(
                        agent_name="coordinator",
                        status="stopped",
                        notes="Stopped because max_agent_steps was exceeded.",
                    )
                )
                break

            seen[current_agent] = seen.get(current_agent, 0) + 1
            if seen[current_agent] > 2:
                state.agent_trace.append(
                    AgentRunRecord(
                        agent_name="coordinator",
                        status="stopped",
                        notes=f"Stopped because {current_agent} looped repeatedly.",
                    )
                )
                break

            agent = self.agents[current_agent]
            result = agent.run(state, settings, options)
            if progress_callback is not None and current_agent in ordered_agents:
                progress_callback(stage_names[current_agent], ordered_agents.index(current_agent) + 1, total_steps)
            current_agent = result.next_agent

        return state
