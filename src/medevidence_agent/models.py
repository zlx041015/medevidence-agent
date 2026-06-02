from dataclasses import dataclass, field


@dataclass
class ClinicalQuestion:
    text: str


@dataclass
class SearchPlan:
    intent: str
    keywords: list[str]
    risk_level: str


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
    needs_human_review: bool = False


@dataclass
class FinalAnswer:
    answer: str
    references: list[str]
    review_flag: bool


@dataclass
class WorkflowState:
    question: ClinicalQuestion
    plan: SearchPlan | None = None
    candidate_sources: list[SourceDocument] = field(default_factory=list)
    evidence_items: list[EvidenceItem] = field(default_factory=list)
    verification: VerificationResult | None = None
    final_answer: FinalAnswer | None = None