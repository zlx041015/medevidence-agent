from medevidence_agent.models import BenchmarkQuestion, MethodRunResult


def retrieval_recall_at_k(result: MethodRunResult, benchmark: BenchmarkQuestion) -> float:
    if not benchmark.gold_sources:
        return 0.0
    hits = sum(1 for source_id in benchmark.gold_sources if source_id in result.retrieved_source_ids)
    return round(hits / len(benchmark.gold_sources), 3)


def citation_precision(result: MethodRunResult, benchmark: BenchmarkQuestion) -> float:
    if not result.retrieved_source_ids:
        return 0.0
    hits = sum(1 for source_id in result.retrieved_source_ids if source_id in benchmark.gold_sources)
    return round(hits / len(result.retrieved_source_ids), 3)


def claim_consistency(result: MethodRunResult, benchmark: BenchmarkQuestion) -> float:
    answer_blob = f"{result.summary_claim} {' '.join(result.extracted_claims)}".lower()
    normalized_claim = benchmark.gold_claim.lower()
    claim_terms = [term for term in normalized_claim.split() if term]

    if not claim_terms:
        compact = normalized_claim.replace(" ", "")
        if not compact:
            return 0.0
        answer_compact = answer_blob.replace(" ", "")
        hits = sum(1 for ch in set(compact) if ch in answer_compact)
        return round(hits / len(set(compact)), 3)

    hits = sum(1 for term in claim_terms if term in answer_blob)
    return round(hits / len(claim_terms), 3)


def hallucination_rate(result: MethodRunResult, benchmark: BenchmarkQuestion) -> float:
    if not result.answer.strip() or not result.references:
        return 1.0
    unsupported = 1 if result.failure_reason else 0
    unsupported += 1 if retrieval_recall_at_k(result, benchmark) == 0 else 0
    return round(unsupported / 2, 3)


def human_review_trigger_rate(result: MethodRunResult, benchmark: BenchmarkQuestion) -> float:
    return 1.0 if benchmark.needs_human_review == result.needs_human_review else 0.0


def score_result(result: MethodRunResult, benchmark: BenchmarkQuestion) -> dict[str, float]:
    return {
        "retrieval_recall_at_k": retrieval_recall_at_k(result, benchmark),
        "citation_precision": citation_precision(result, benchmark),
        "claim_consistency": claim_consistency(result, benchmark),
        "hallucination_rate": hallucination_rate(result, benchmark),
        "human_review_trigger_rate": human_review_trigger_rate(result, benchmark),
    }
