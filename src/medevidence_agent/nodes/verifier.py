from collections import Counter
from typing import Optional

from medevidence_agent.models import EvidenceItem, VerificationResult
from medevidence_agent.tools.mesh import detect_mesh_terms, load_mesh_terms
from medevidence_agent.config import settings


EVIDENCE_LEVEL_WEIGHTS = {
    "guideline": 0.16,
    "consensus": 0.14,
    "systematic_review": 0.13,
    "meta_analysis": 0.13,
    "review": 0.08,
    "trial": 0.08,
    "knowledge_base": 0.07,
    "pubmed_article": 0.05,
    "case_report": 0.03,
    "blog": -0.04,
}


TOPIC_KEYWORDS = {
    "diabetes": ["diabetes", "albuminuria", "proteinuria", "glycemic"],
    "hypertension": ["hypertension", "blood pressure"],
    "kidney": ["kidney", "renal", "albuminuria", "ckd"],
    "thyroid": ["thyroid", "goiter"],
    "lipid": ["lipid", "ldl", "hyperlipidemia", "cholesterol"],
    "coronary": ["coronary", "cardiovascular", "secondary prevention"],
    "heart_failure": ["heart failure", "cardiac", "decompensation"],
    "af": ["atrial fibrillation", "stroke risk", "anticoagulation"],
    "stroke": ["stroke", "rehabilitation", "recurrence"],
    "copd": ["copd", "exacerbation", "inhaler"],
    "asthma": ["asthma", "inhaled", "control"],
    "pneumonia": ["pneumonia", "infection", "severity"],
    "tb": ["tuberculosis", "infection control", "recurrence"],
    "anemia": ["anemia", "hemoglobin", "ferritin", "iron deficiency"],
    "osteoporosis": ["osteoporosis", "fracture", "bone density"],
    "gout": ["gout", "urate", "joint pain"],
    "ra": ["rheumatoid arthritis", "joint inflammation"],
    "oa": ["osteoarthritis", "joint pain", "function"],
    "gerd": ["reflux", "gerd", "heartburn"],
    "ulcer": ["ulcer", "bleeding risk", "peptic"],
    "gastroenteritis": ["gastroenteritis", "dehydration", "diarrhea"],
    "fatty_liver": ["fatty liver", "metabolic risk", "liver"],
    "hbv": ["hepatitis b", "hbv", "liver function"],
    "uti": ["urinary tract infection", "uti", "infection"],
    "bph": ["bph", "prostatic", "urinary symptoms"],
    "stone": ["kidney stone", "stone", "recurrence"],
    "depression": ["depression", "mood symptoms", "relapse"],
    "anxiety": ["anxiety", "symptom control", "trigger"],
    "insomnia": ["insomnia", "sleep hygiene", "sleep"],
    "migraine": ["migraine", "headache", "trigger"],
    "eczema": ["eczema", "itch", "skin barrier"],
    "urticaria": ["urticaria", "allergy", "itch"],
    "acne": ["acne", "skin care"],
    "obesity": ["obesity", "weight management", "metabolic risk"],
    "screening": ["screening", "monitoring", "follow-up"],
    "treatment": ["treatment", "therapy", "drug", "management", "first-line"],
    "risk": ["risk", "complication", "target"],
}


def _build_question_keywords(question_text: str) -> list[str]:
    lowered = question_text.lower()
    triggers = {
        "diabetes": ["糖尿病", "diabetes"],
        "hypertension": ["高血压", "hypertension"],
        "kidney": ["肾", "ckd", "kidney", "renal", "蛋白尿", "白蛋白尿"],
        "thyroid": ["甲状腺", "thyroid", "goiter"],
        "lipid": ["高脂血症", "血脂", "cholesterol", "ldl", "hyperlipidemia"],
        "coronary": ["冠心病", "coronary", "cad", "心绞痛"],
        "heart_failure": ["心力衰竭", "heart failure"],
        "af": ["房颤", "atrial fibrillation", "af"],
        "stroke": ["脑卒中", "stroke"],
        "copd": ["慢阻肺", "copd"],
        "asthma": ["哮喘", "asthma"],
        "pneumonia": ["肺炎", "pneumonia", "cap"],
        "tb": ["结核", "tuberculosis", "tb"],
        "anemia": ["贫血", "anemia", "缺铁"],
        "osteoporosis": ["骨质疏松", "osteoporosis"],
        "gout": ["痛风", "gout"],
        "ra": ["类风湿", "rheumatoid arthritis", "ra"],
        "oa": ["骨关节炎", "osteoarthritis"],
        "gerd": ["胃食管反流", "gerd", "reflux"],
        "ulcer": ["溃疡", "ulcer", "消化性溃疡"],
        "gastroenteritis": ["胃肠炎", "gastroenteritis"],
        "fatty_liver": ["脂肪肝", "fatty liver"],
        "hbv": ["乙肝", "hepatitis b", "hbv"],
        "uti": ["尿路感染", "urinary tract infection", "uti"],
        "bph": ["前列腺增生", "bph"],
        "stone": ["肾结石", "kidney stone", "stone"],
        "depression": ["抑郁", "depression"],
        "anxiety": ["焦虑", "anxiety"],
        "insomnia": ["失眠", "insomnia"],
        "migraine": ["偏头痛", "migraine"],
        "eczema": ["湿疹", "eczema"],
        "urticaria": ["荨麻疹", "urticaria"],
        "acne": ["痤疮", "acne"],
        "obesity": ["肥胖", "obesity"],
        "screening": ["筛查", "screening", "monitoring", "随访"],
        "treatment": ["治疗", "用药", "treatment", "therapy"],
        "risk": ["风险", "并发症", "complication", "target"],
    }

    keywords: list[str] = []
    for topic, values in triggers.items():
        if any(value in question_text or value in lowered for value in values):
            keywords.extend(TOPIC_KEYWORDS[topic])

    return list(dict.fromkeys(keywords))


def _compute_topic_coverage(question_keywords: list[str], evidence_items: list[EvidenceItem]) -> float:
    if not question_keywords or not evidence_items:
        return 0.0
    combined_claims = " ".join(item.claim for item in evidence_items).lower()
    hits = sum(1 for keyword in question_keywords if keyword.lower() in combined_claims)
    return round(hits / len(question_keywords), 3)


def _detect_conflicts(evidence_items: list[EvidenceItem]) -> list[str]:
    conflicts: list[str] = []
    claims_blob = " ".join(item.claim.lower() for item in evidence_items)
    if "not recommended" in claims_blob and "recommended" in claims_blob:
        conflicts.append("Retrieved evidence contains both recommended and not recommended statements.")
    if "insufficient evidence" in claims_blob and (
        "first-line" in claims_blob or "recommended" in claims_blob
    ):
        conflicts.append("Some sources support action while others describe evidence as insufficient.")
    source_types = Counter(item.source_type for item in evidence_items)
    if source_types.get("blog", 0) >= 1 and len(evidence_items) <= 2:
        conflicts.append("Evidence pool relies on low-quality blog-like content.")
    return conflicts


def verify_evidence(
    question_text: str,
    evidence_items: list[EvidenceItem],
    confidence_threshold: float,
    mesh_terms: Optional[list[str]] = None,
) -> VerificationResult:
    mesh_terms = mesh_terms or []
    if not evidence_items:
        return VerificationResult(
            summary_claim="No sufficient evidence was retrieved for a reliable clinical summary.",
            confidence=0.0,
            supporting_evidence=[],
            conflicts=["No usable evidence was available for verification."],
            check_results={
                "topic_alignment": "failed",
                "support_strength": "failed",
                "evidence_level": "failed",
                "timeliness": "failed",
                "conflict_check": "failed",
            },
            evidence_coverage=0.0,
            mesh_topic_alignment=[],
            needs_human_review=True,
        )

    avg_score = sum(item.score for item in evidence_items) / len(evidence_items)
    recent_count = sum(1 for item in evidence_items if item.year >= 2020)
    evidence_level_bonus = sum(EVIDENCE_LEVEL_WEIGHTS.get(item.source_type, 0.04) for item in evidence_items)
    evidence_level_bonus = min(evidence_level_bonus, 0.28)
    question_keywords = _build_question_keywords(question_text)
    topic_coverage = _compute_topic_coverage(question_keywords, evidence_items)
    conflicts = _detect_conflicts(evidence_items)
    mesh_map = load_mesh_terms(settings.mesh_terms_path)
    evidence_mesh_hits = detect_mesh_terms(" ".join(item.support_text for item in evidence_items), mesh_map)
    mesh_matches = [term for term in mesh_terms if term in evidence_mesh_hits]

    support_strength = round(
        sum(1 for item in evidence_items if len(item.support_text.split()) >= 8) / len(evidence_items),
        3,
    )
    timeliness_score = round(min(recent_count, 3) / 3, 3)

    confidence = avg_score * 0.35
    confidence += min(len(evidence_items), 5) * 0.05
    confidence += evidence_level_bonus
    confidence += topic_coverage * 0.12
    confidence += min(len(mesh_matches), 3) * 0.03
    confidence += support_strength * 0.08
    confidence += timeliness_score * 0.07
    if conflicts:
        confidence -= min(0.12, 0.05 * len(conflicts))
    confidence = round(max(0.0, min(confidence, 1.0)), 3)

    if any(item.source_type == "guideline" for item in evidence_items):
        summary_claim = "High-level guideline evidence is available and supports a cautious clinical summary."
    elif len(evidence_items) >= 3 and recent_count >= 1:
        summary_claim = "Multiple evidence sources are available and can support a preliminary summary."
    elif len(evidence_items) >= 2:
        summary_claim = "Limited but usable evidence is available for a preliminary summary."
    else:
        summary_claim = "Only sparse evidence is available, so the summary should be treated as tentative."

    lowered = question_text.lower()
    if "并发症" in question_text or "complication" in lowered or "risk" in lowered:
        summary_claim += " The current evidence is more suitable for complication or risk identification."
    elif "治疗" in question_text or "用药" in question_text or "treatment" in lowered or "therapy" in lowered:
        summary_claim += " The evidence is mainly useful for treatment-oriented recommendation synthesis."
    elif "筛查" in question_text or "screening" in lowered or "monitoring" in lowered:
        summary_claim += " The evidence is mainly useful for screening and follow-up planning."

    check_results = {
        "topic_alignment": "passed" if topic_coverage >= 0.35 else "warning",
        "support_strength": "passed" if support_strength >= 0.6 else "warning",
        "evidence_level": "passed" if evidence_level_bonus >= 0.1 else "warning",
        "timeliness": "passed" if timeliness_score >= 0.34 else "warning",
        "mesh_alignment": "passed" if mesh_matches else "warning",
        "conflict_check": "warning" if conflicts else "passed",
    }

    if topic_coverage < 0.2:
        conflicts.append("Evidence claims only weakly match the question topic.")
    if support_strength < 0.4:
        conflicts.append("Several extracted evidence items lack strong supporting text.")
    if timeliness_score == 0.0:
        conflicts.append("No recent evidence source was found.")
    if mesh_terms and not mesh_matches:
        conflicts.append("Evidence does not align well with expected MeSH disease topics.")
    if all(item.source_type == "case_report" for item in evidence_items):
        conflicts.append("All supporting evidence comes from case reports, which is low-level evidence.")

    needs_human_review = confidence < confidence_threshold or bool(conflicts)

    return VerificationResult(
        summary_claim=summary_claim,
        confidence=confidence,
        supporting_evidence=evidence_items,
        conflicts=conflicts,
        check_results=check_results,
        evidence_coverage=topic_coverage,
        mesh_topic_alignment=mesh_matches,
        needs_human_review=needs_human_review,
    )
