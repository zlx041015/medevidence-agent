from medevidence_agent.models import EvidenceItem, VerificationResult


def verify_evidence(
    question_text: str,
    evidence_items: list[EvidenceItem],
    confidence_threshold: float,
) -> VerificationResult:
    if not evidence_items:
        return VerificationResult(
            summary_claim="当前未检索到足够证据，无法形成可靠结论。",
            confidence=0.0,
            supporting_evidence=[],
            conflicts=["没有获得可用于总结的来源证据。"],
            needs_human_review=True,
        )

    question_lower = question_text.lower()
    avg_score = sum(item.score for item in evidence_items) / len(evidence_items)
    source_count = len(evidence_items)
    recent_count = sum(1 for item in evidence_items if item.year >= 2020)

    type_weights = {
        "guideline": 0.14,
        "systematic_review": 0.12,
        "meta_analysis": 0.12,
        "review": 0.08,
        "trial": 0.08,
        "case_report": 0.03,
        "pubmed_article": 0.05,
    }
    type_bonus = sum(type_weights.get(item.source_type, 0.05) for item in evidence_items)

    confidence = avg_score * 0.4
    confidence += min(source_count, 5) * 0.06
    confidence += min(recent_count, 3) * 0.05
    confidence += min(type_bonus, 0.25)
    confidence = min(1.0, round(confidence, 3))

    conflicts: list[str] = []

    if source_count < 2:
        conflicts.append("当前可用证据来源数量较少。")

    if recent_count == 0:
        conflicts.append("当前证据缺少较新的文献来源。")

    if all(item.source_type == "case_report" for item in evidence_items):
        conflicts.append("当前证据主要来自病例报告，证据等级较弱。")

    question_keywords: list[str] = []
    if "癌" in question_text or "cancer" in question_lower:
        question_keywords.extend(["癌", "cancer", "tumor", "tumour", "oncology"])
    if "甲状腺" in question_text or "thyroid" in question_lower:
        question_keywords.extend(["甲状腺", "thyroid", "goiter"])
    if "胰腺" in question_text or "pancreatic" in question_lower:
        question_keywords.extend(["胰腺", "pancreatic"])
    if "高血压" in question_text or "hypertension" in question_lower:
        question_keywords.extend(["高血压", "hypertension", "blood pressure"])
    if "糖尿病" in question_text or "diabetes" in question_lower:
        question_keywords.extend(["糖尿病", "diabetes"])
    if "并发症" in question_text or "complication" in question_lower:
        question_keywords.extend(["并发症", "complication"])
    if (
        "用药" in question_text
        or "治疗" in question_text
        or "treatment" in question_lower
        or "therapy" in question_lower
    ):
        question_keywords.extend(["用药", "治疗", "treatment", "therapy", "drug"])

    combined_claims = " ".join(item.claim for item in evidence_items).lower()
    unique_keywords = list(dict.fromkeys(question_keywords))
    keyword_hits = sum(1 for keyword in unique_keywords if keyword.lower() in combined_claims)

    if unique_keywords and keyword_hits == 0:
        conflicts.append("当前证据与问题主题匹配度较低。")
    elif unique_keywords and keyword_hits <= max(1, len(unique_keywords) // 5):
        conflicts.append("当前证据仅部分覆盖问题主题。")

    if any(item.source_type == "guideline" for item in evidence_items):
        summary_claim = "当前已有较高层级来源证据，可用于支持初步医学总结。"
    elif source_count >= 3 and recent_count >= 1:
        summary_claim = "当前已有多条来源证据可用于支持初步医学总结。"
    elif source_count >= 2:
        summary_claim = "当前已有有限但可用的来源证据，可形成初步总结。"
    else:
        summary_claim = "当前证据较少，仅能形成非常初步的总结。"

    if "并发症" in question_text or "complication" in question_lower:
        summary_claim += " 现有证据更适合用于识别相关并发症或风险信息。"
    elif (
        "用药" in question_text
        or "治疗" in question_text
        or "treatment" in question_lower
        or "therapy" in question_lower
    ):
        summary_claim += " 现有证据更适合用于提炼治疗或用药相关线索。"

    return VerificationResult(
        summary_claim=summary_claim,
        confidence=confidence,
        supporting_evidence=evidence_items,
        conflicts=conflicts,
        needs_human_review=confidence < confidence_threshold or bool(conflicts),
    )
