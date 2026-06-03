import json

from medevidence_agent.config import Settings
from medevidence_agent.llm import chat_completion
from medevidence_agent.models import FinalAnswer, VerificationResult


def _build_conclusion_text(question_text: str, result: VerificationResult) -> str:
    if not result.supporting_evidence:
        return "当前未获得足够证据，暂无法形成可靠的医学总结。"

    lowered = question_text.lower()
    claims = [item.claim.strip() for item in result.supporting_evidence[:4] if item.claim.strip()]

    if "筛查" in question_text or "screening" in lowered or "monitoring" in lowered:
        return "现有证据提示，这一问题的核心在于建立规范的筛查与随访框架，重点应围绕高风险并发症识别、关键监测指标以及长期随访安排展开。"

    if "随访" in question_text or "follow-up" in lowered or "follow up" in lowered:
        return "现有证据提示，这一问题的核心在于长期动态评估病情变化、风险趋势和治疗反应，并根据随访结果调整后续管理策略。"

    if "风险" in question_text or "并发症" in question_text or "risk" in lowered or "complication" in lowered:
        return "现有证据提示，这类问题的重点在于识别高风险人群、判断主要并发症或不良结局风险，并据此进行分层管理。"

    if "治疗" in question_text or "用药" in question_text or "treatment" in lowered or "therapy" in lowered:
        if claims:
            lead = claims[0]
            support = claims[1] if len(claims) > 1 else ""
            if support:
                return f"结合当前检索到的证据，这一问题的核心回答是：{lead} 同时还需要结合 {support} 所提示的风险分层、长期管理或器官保护策略进行综合决策。"
            return f"结合当前检索到的证据，这一问题的核心回答是：{lead}"

    if claims:
        return f"结合当前检索到的证据，这一问题的核心回答可概括为：{claims[0]}"
    return result.summary_claim


def write_answer_rule_based(question_text: str, result: VerificationResult) -> FinalAnswer:
    references = [
        f"{index}. {item.title} ({item.year}) - {item.url}"
        for index, item in enumerate(result.supporting_evidence, start=1)
    ]

    evidence_points = []
    for item in result.supporting_evidence[:4]:
        evidence_points.append(f"- {item.claim}")

    conclusion_text = _build_conclusion_text(question_text, result)
    risk_line = "需要人工审核" if result.needs_human_review else "可作为初步参考"
    conflict_block = ""
    if result.conflicts:
        conflict_block = "\n- 风险：" + "；".join(result.conflicts)

    answer = (
        "结论：\n"
        f"{conclusion_text}\n\n"
        "证据要点：\n"
        + ("\n".join(evidence_points) if evidence_points else "- 暂无可展示证据要点")
        + "\n\n"
        f"置信度与风险：\n- 置信度：{result.confidence:.3f}\n- 状态：{risk_line}"
        f"{conflict_block}"
    )

    return FinalAnswer(
        answer=answer,
        references=references,
        review_flag=result.needs_human_review,
    )


def write_answer_with_llm(question_text: str, result: VerificationResult, settings: Settings) -> FinalAnswer:
    references = [
        f"{index}. {item.title} ({item.year}) - {item.url}"
        for index, item in enumerate(result.supporting_evidence, start=1)
    ]

    evidence_summary = []
    for item in result.supporting_evidence:
        evidence_summary.append(
            {
                "title": item.title,
                "year": item.year,
                "source_type": item.source_type,
                "claim": item.claim,
                "support_text": item.support_text,
                "score": item.score,
            }
        )

    system_prompt = """
你是一个医学证据总结助手。你的任务不是新增医学推断，而是把已经核验过的结果整理成清晰、克制、适合阅读的中文输出。
请严格输出 JSON，不要输出任何额外解释。JSON 格式如下：
{
  "answer": "最终展示给用户的排版后正文"
}

正文排版要求：
1. 使用以下固定结构：
结论：
...

证据要点：
- ...
- ...

置信度与风险：
- 置信度：...
- 状态：...
- 风险：...

2. “结论”部分必须直接回答原始问题，而不是简单拼接证据要点
3. “结论”部分只总结医学信息本身，不要把“匹配度偏弱”“需要人工审核”等可靠性判断写进结论段
4. 可靠性、不确定性、人工审核提示统一放在“置信度与风险”部分
5. 证据要点控制在 2 到 4 条
6. 只基于给定核验结果和证据内容输出，不要编造新事实
7. 不要输出 markdown 代码块
""".strip()

    user_prompt = f"""原始问题：
{question_text}

核验结论：
{result.summary_claim}

建议性结论文本：
{_build_conclusion_text(question_text, result)}

置信度：
{result.confidence}

是否需要人工审核：
{result.needs_human_review}

冲突信息：
{json.dumps(result.conflicts, ensure_ascii=False)}

证据列表：
{json.dumps(evidence_summary, ensure_ascii=False, indent=2)}
"""

    raw = chat_completion(
        settings=settings,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        temperature=0.2,
    )

    data = json.loads(raw)

    return FinalAnswer(
        answer=data["answer"],
        references=references,
        review_flag=result.needs_human_review,
    )


def write_answer(question_text: str, result: VerificationResult, settings: Settings) -> FinalAnswer:
    try:
        return write_answer_with_llm(question_text, result, settings)
    except Exception as exc:
        print(f"[Writer fallback] LLM writer failed: {exc}")
        return write_answer_rule_based(question_text, result)
