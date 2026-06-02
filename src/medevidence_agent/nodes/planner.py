from medevidence_agent.models import ClinicalQuestion, SearchPlan


def build_search_plan(question: ClinicalQuestion) -> SearchPlan:
    text = question.text.strip()
    lowered = text.lower()

    keywords = ["diabetes", "hypertension", "guideline"]

    if "高血压" in text or "hypertension" in lowered:
        keywords.append("blood pressure")
        keywords.append("antihypertensive")

    if "2型糖尿病" in text or "type 2 diabetes" in lowered:
        keywords.append("type 2 diabetes")

    if "一线" in text or "first-line" in lowered or "首选" in text:
        keywords.append("first-line")
        keywords.append("ACE inhibitor")
        keywords.append("ARB")

    if "蛋白尿" in text or "albuminuria" in lowered:
        keywords.append("albuminuria")

    if "肾病" in text or "chronic kidney disease" in lowered or "ckd" in lowered:
        keywords.append("chronic kidney disease")

    if "目标" in text or "target" in lowered:
        keywords.append("blood pressure targets")
        keywords.append("individualized targets")

    if "生活方式" in text or "lifestyle" in lowered:
        keywords.append("lifestyle")
        keywords.append("exercise")
        keywords.append("diet")

    keywords = list(dict.fromkeys(keywords))

    return SearchPlan(
        intent="Find evidence-based management suggestions for the clinical question.",
        keywords=keywords,
        risk_level="high",
    )