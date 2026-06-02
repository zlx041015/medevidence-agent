from medevidence_agent.models import EvidenceItem, VerificationResult


def verify_evidence(
    evidence_items: list[EvidenceItem],
    confidence_threshold: float,
) -> VerificationResult:
    if not evidence_items:
        return VerificationResult(
            summary_claim="当前未检索到足够证据，无法形成可靠结论。",
            confidence=0.0,
            supporting_evidence=[],
            conflicts=["没有证据通过检索阈值过滤。"],
            needs_human_review=True,
        )

    avg_score = sum(item.score for item in evidence_items) / len(evidence_items)
    guideline_count = sum(1 for item in evidence_items if item.source_type == "guideline")

    supports_ace_arb = any("ACEI/ARB" in item.claim or "ACEI" in item.claim for item in evidence_items)
    supports_lifestyle = any("生活方式" in item.claim for item in evidence_items)
    supports_individualized = any("个体化" in item.claim for item in evidence_items)

    confidence = avg_score * 0.5 + guideline_count * 0.1

    if supports_ace_arb:
        confidence += 0.1
    if supports_lifestyle:
        confidence += 0.05
    if supports_individualized:
        confidence += 0.05

    confidence = min(1.0, round(confidence, 3))

    conflicts = []

    if any(item.source_type == "blog" for item in evidence_items):
        conflicts.append("证据池中混入了低质量、非指南类来源。")

    if not supports_ace_arb:
        conflicts.append("当前证据未明确支持 ACEI/ARB 作为核心治疗选择。")

    summary_parts = []

    if supports_ace_arb:
        summary_parts.append("较高质量证据支持 ACEI/ARB 可作为常见的一线降压治疗选择")
    else:
        summary_parts.append("当前证据对一线药物选择的支持仍不足")

    if supports_lifestyle:
        summary_parts.append("应结合生活方式干预")

    if supports_individualized:
        summary_parts.append("并根据患者情况设置个体化管理目标")

    summary_claim = "；".join(summary_parts) + "。"

    return VerificationResult(
        summary_claim=summary_claim,
        confidence=confidence,
        supporting_evidence=evidence_items,
        conflicts=conflicts,
        needs_human_review=confidence < confidence_threshold or bool(conflicts),
    )