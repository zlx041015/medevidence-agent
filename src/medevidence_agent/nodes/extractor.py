import json

from medevidence_agent.config import Settings
from medevidence_agent.llm import chat_completion
from medevidence_agent.models import EvidenceItem, SourceDocument


def build_rule_based_claim_from_content(content: str) -> str:
    lowered = content.lower()

    mentions_ace_arb = "ace inhibitors" in lowered or "arbs" in lowered or "arb" in lowered
    mentions_lifestyle = "lifestyle" in lowered or "diet" in lowered or "exercise" in lowered
    mentions_individualized = "individualized" in lowered

    if mentions_ace_arb and mentions_lifestyle and mentions_individualized:
        return "ACEI/ARB 常作为一线降压选择，并应结合生活方式干预和个体化管理目标。"

    if mentions_ace_arb and mentions_lifestyle:
        return "ACEI/ARB 常作为一线降压选择，并应结合生活方式干预。"

    if mentions_ace_arb:
        return "ACEI/ARB 常作为相关疾病管理中的重要治疗选择。"

    if mentions_lifestyle:
        return "该来源强调了生活方式干预在疾病管理中的重要性。"

    return "该来源支持当前问题需要结合临床背景进行综合管理。"


def extract_evidence_rule_based(candidates: list[SourceDocument]) -> list[EvidenceItem]:
    evidence = []

    for item in candidates:
        claim = build_rule_based_claim_from_content(item.content)

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


def extract_single_evidence_with_llm(item: SourceDocument, settings: Settings) -> EvidenceItem:
    system_prompt = """
你是一个医学证据抽取助手。你的任务不是回答问题，而是从单条来源内容中抽取结构化证据。

请严格输出 JSON，不要输出任何额外解释。JSON 格式如下：
{
  "claim": "一句中文结论，概括该来源支持的核心观点",
  "support_text": "从原文中摘取最能支持 claim 的一句或两句内容"
}

要求：
1. claim 用中文表达
2. claim 应尽量简洁、客观，不要夸大
3. support_text 必须来自原始内容，不要编造
4. 不要输出 markdown，不要输出代码块
""".strip()

    user_prompt = f"""来源标题：{item.title}
来源类型：{item.source_type}
年份：{item.year}
原始内容：
{item.content}
"""

    raw = chat_completion(
        settings=settings,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        temperature=0.2,
    )

    data = json.loads(raw)

    return EvidenceItem(
        source_id=item.source_id,
        title=item.title,
        claim=data["claim"],
        support_text=data["support_text"],
        source_type=item.source_type,
        year=item.year,
        url=item.url,
        score=item.relevance_score,
    )


def extract_evidence(candidates: list[SourceDocument], settings: Settings) -> list[EvidenceItem]:
    try:
        return [extract_single_evidence_with_llm(item, settings) for item in candidates]
    except Exception as exc:
        print(f"[Extractor fallback] LLM extractor failed: {exc}")
        return extract_evidence_rule_based(candidates)


def extract_evidence_with_mode(
    candidates: list[SourceDocument],
    settings: Settings,
    mode: str = "auto",
) -> list[EvidenceItem]:
    if mode == "rule":
        return extract_evidence_rule_based(candidates)
    return extract_evidence(candidates, settings)
