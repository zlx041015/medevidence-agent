import json

from medevidence_agent.config import Settings
from medevidence_agent.llm import chat_completion
from medevidence_agent.models import FinalAnswer, VerificationResult


def write_answer_rule_based(result: VerificationResult) -> FinalAnswer:
    references = [
        f"{index}. {item.title} ({item.year}) - {item.url}"
        for index, item in enumerate(result.supporting_evidence, start=1)
    ]

    evidence_points = []
    for item in result.supporting_evidence[:3]:
        evidence_points.append(f"- {item.claim}")

    risk_line = "需要人工审核" if result.needs_human_review else "可作为初步参考"
    conflict_block = ""
    if result.conflicts:
        conflict_block = "\n已识别风险：\n" + "\n".join(f"- {conflict}" for conflict in result.conflicts)

    answer = (
        "结论：\n"
        f"{result.summary_claim}\n\n"
        "证据要点：\n"
        + ("\n".join(evidence_points) if evidence_points else "- 暂无可展示证据要点")
        + "\n\n"
        f"置信度与风险：\n- 置信度：{result.confidence:.2f}\n- 状态：{risk_line}"
        f"{conflict_block}"
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
你是一个医学证据总结助手。你的任务不是新增医学推断，而是把已核验的结果整理成清晰、克制、适合阅读的中文输出。

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

2. 不要写成长段重复叙述
3. 证据要点控制在 2 到 4 条
4. 只基于给定核验结果和证据内容输出，不要编造新事实
5. 如果需要人工审核，必须明确写出“需要人工审核”
6. 不要输出 markdown 代码块
""".strip()

    user_prompt = f"""核验结论：
{result.summary_claim}

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


def write_answer(result: VerificationResult, settings: Settings) -> FinalAnswer:
    try:
        return write_answer_with_llm(result, settings)
    except Exception as exc:
        print(f"[Writer fallback] LLM writer failed: {exc}")
        return write_answer_rule_based(result)
