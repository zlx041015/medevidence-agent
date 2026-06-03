from medevidence_agent.models import SearchPlan, SourceDocument


def split_disease_and_support_terms(query_terms: list[str]) -> tuple[list[str], list[str]]:
    disease_markers = [
        "diabetes",
        "hypertension",
        "kidney",
        "renal",
        "thyroid",
        "goiter",
        "cholesterol",
        "hyperlipidemia",
        "coronary",
        "heart failure",
        "atrial fibrillation",
        "stroke",
        "copd",
        "asthma",
        "pneumonia",
        "tuberculosis",
        "anemia",
        "osteoporosis",
        "gout",
        "arthritis",
        "reflux",
        "ulcer",
        "gastroenteritis",
        "fatty liver",
        "hepatitis",
        "urinary tract infection",
        "prostatic hyperplasia",
        "kidney stone",
        "depression",
        "anxiety",
        "insomnia",
        "migraine",
        "eczema",
        "urticaria",
        "acne",
        "obesity",
        "cancer",
    ]
    disease_terms: list[str] = []
    support_terms: list[str] = []
    for term in query_terms:
        lowered = term.lower()
        if any(marker in lowered for marker in disease_markers):
            disease_terms.append(term)
        else:
            support_terms.append(term)
    return disease_terms, support_terms


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
    disease_terms, support_terms = split_disease_and_support_terms(plan.keywords)

    for source in sources:
        disease_overlap = keyword_overlap_score(disease_terms, source.content) if disease_terms else 0.0
        support_overlap = keyword_overlap_score(support_terms, source.content) if support_terms else 0.0
        overlap = 0.75 * disease_overlap + 0.25 * support_overlap
        final_score = 0.6 * overlap + 0.4 * source.quality_score
        if disease_terms and disease_overlap == 0:
            final_score -= 0.18
        source.relevance_score = round(final_score, 3)

        if source.relevance_score >= evidence_score_threshold:
            rescored.append(source)

    rescored.sort(key=lambda item: item.relevance_score, reverse=True)

    return rescored[:top_k]
