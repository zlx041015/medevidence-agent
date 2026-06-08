from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ClinicalQuestion:
    text: str


@dataclass
class SearchPlan:
    intent: str
    keywords: list[str]
    risk_level: str
    mesh_terms: list[str] = field(default_factory=list)


@dataclass
class SourceDocument:
    source_id: str
    title: str
    source_type: str
    year: int
    url: str
    quality_score: float
    content: str
    relevance_score: float = 0.0


@dataclass
class EvidenceItem:
    source_id: str
    title: str
    claim: str
    support_text: str
    source_type: str
    year: int
    url: str
    score: float


@dataclass
class VerificationResult:
    summary_claim: str
    confidence: float
    supporting_evidence: list[EvidenceItem] = field(default_factory=list)
    conflicts: list[str] = field(default_factory=list)
    check_results: dict[str, str] = field(default_factory=dict)
    evidence_coverage: float = 0.0
    mesh_topic_alignment: list[str] = field(default_factory=list)
    needs_human_review: bool = False


@dataclass
class FinalAnswer:
    answer: str
    references: list[str]
    review_flag: bool


@dataclass
class AgentRunRecord:
    agent_name: str
    status: str
    notes: str = ""


@dataclass
class WorkflowState:
    question: ClinicalQuestion
    plan: Optional[SearchPlan] = None
    candidate_sources: list[SourceDocument] = field(default_factory=list)
    evidence_items: list[EvidenceItem] = field(default_factory=list)
    verification: Optional[VerificationResult] = None
    final_answer: Optional[FinalAnswer] = None
    agent_trace: list[AgentRunRecord] = field(default_factory=list)


@dataclass
class WorkflowOptions:
    use_planner: bool = True
    use_verifier: bool = True
    use_rag: bool = True
    use_source_type_weighting: bool = True
    extractor_mode: str = "auto"
    source_mode_override: Optional[str] = None
    max_agent_steps: int = 12


@dataclass
class BenchmarkQuestion:
    question_id: str
    question: str
    question_type: str
    risk_level: str
    gold_keywords: list[str]
    gold_sources: list[str]
    gold_claim: str
    needs_human_review: bool
    mesh_terms: list[str] = field(default_factory=list)


@dataclass
class MethodRunResult:
    method_name: str
    question_id: str
    question: str
    answer: str
    references: list[str]
    retrieved_source_ids: list[str]
    extracted_claims: list[str]
    summary_claim: str
    confidence: float
    needs_human_review: bool
    conflicts: list[str] = field(default_factory=list)
    check_results: dict[str, str] = field(default_factory=dict)
    failure_reason: str = ""
