from medevidence_agent.models import FinalAnswer, VerificationResult


def write_answer(result: VerificationResult) -> FinalAnswer:
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
