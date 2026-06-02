import json

from medevidence_agent.config import Settings
from medevidence_agent.llm import chat_completion
from medevidence_agent.models import FinalAnswer, VerificationResult


def write_answer_rule_based(result: VerificationResult) -> FinalAnswer:
    references = [
        f"{index}. {item.title} ({item.year}) - {item.url}"
        for index, item in enumerate(result.supporting_evidence, start=1)
    ]

    uncertainty_line = ""
    if result.needs_human_review:
        uncertainty_line = (
            "\n\n提示：当前结果尚未完全满足置信度要求，或检测到了冲突信息，"
            "建议由临床专业人员进一步审核。"
        )

    answer = (
        "初步证据结论：\n"
        f"{result.summary_claim}\n\n"
        f"置信度：{result.confidence:.2f}。"
        f"{uncertainty_line}"
    )

    return FinalAnswer(
        answer=answer,
        references=references,
        review_flag=result.needs_human_review,
    )


def write_answer_with_llm(result: VerificationResult, settings: Settings) -> FinalAnswer:
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
你是一个医学证据总结助手。你的任务不是做新的医学推断，而是根据已经核验过的结果，生成简洁、专业、克制的中文总结。

请严格输出 JSON，不要输出任何额外解释。JSON 格式如下：
{
  "answer": "给用户展示的中文总结正文"
}

要求：
1. 只基于提供的核验结果和证据信息写总结
2. 不要编造新的医学事实
3. 语气要专业、克制
4. 如果需要人工审核，应在正文中明确提醒
5. 不要输出 markdown 代码块
""".strip()

    user_prompt = f"""核验结论：
{result.summary_claim}

置信度：
{result.confidence}

是否需要人工审核：
{result.needs_human_review}

冲突信息：
{result.conflicts}

证据列表：
{json.dumps(evidence_summary, ensure_ascii=False, indent=2)}
"""

    raw = chat_completion(
        settings=settings,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        temperature=0.3,
    )

    data = json.loads(raw)

    return FinalAnswer(
        answer=data["answer"],
        references=references,
        review_flag=result.needs_human_review,
    )


def write_answer(result: VerificationResult, settings: Settings) -> FinalAnswer:
    try:
        return write_answer_with_llm(result, settings)
    except Exception as exc:
        print(f"[Writer fallback] LLM writer failed: {exc}")
        return write_answer_rule_based(result)