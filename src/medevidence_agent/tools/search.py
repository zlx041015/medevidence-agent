from medevidence_agent.models import SearchPlan, SourceDocument


def keyword_overlap_score(query_terms: list[str], content: str) -> float:
    lowered_content = content.lower()
    matches = sum(1 for term in query_terms if term.lower() in lowered_content)

    if not query_terms:
        return 0.0

    return matches / len(query_terms)


def retrieve_sources(
    plan: SearchPlan,
    sources: list[SourceDocument],
    top_k: int,
    evidence_score_threshold: float,
) -> list[SourceDocument]:
    rescored = []

    for source in sources:
        overlap = keyword_overlap_score(plan.keywords, source.content)
        final_score = 0.6 * overlap + 0.4 * source.quality_score
        source.relevance_score = round(final_score, 3)

        if source.relevance_score >= evidence_score_threshold:
            rescored.append(source)

    rescored.sort(key=lambda item: item.relevance_score, reverse=True)

    return rescored[:top_k]