from medevidence_agent.models import EvidenceItem, SourceDocument


def build_claim_from_content(content: str) -> str:
    lowered = content.lower()

    mentions_ace_arb = "ace inhibitors" in lowered or "arbs" in lowered or "arb" in lowered
    mentions_lifestyle = "lifestyle" in lowered or "diet" in lowered or "exercise" in lowered
    mentions_individualized = "individualized" in lowered

    if mentions_ace_arb and mentions_lifestyle and mentions_individualized:
        return "ACEI/ARB 常作为一线降压选择，并应结合生活方式干预和个体化管理目标。"

    if mentions_ace_arb and mentions_lifestyle:
        return "ACEI/ARB 常作为一线降压选择，并应结合生活方式干预。"

    if mentions_ace_arb:
        return "ACEI/ARB 常作为糖尿病合并高血压患者的一线降压选择。"

    if mentions_lifestyle:
        return "生活方式干预是糖尿病合并高血压管理的重要组成部分。"

    return "该来源支持糖尿病合并高血压患者需要综合管理。"


def extract_evidence(candidates: list[SourceDocument]) -> list[EvidenceItem]:
    evidence = []

    for item in candidates:
        claim = build_claim_from_content(item.content)

        evidence.append(
            EvidenceItem(
                source_id=item.source_id,
                title=item.title,
                claim=claim,
                support_text=item.content,
                source_type=item.source_type,
                year=item.year,
                url=item.url,
                score=item.relevance_score,
            )
        )

    return evidence