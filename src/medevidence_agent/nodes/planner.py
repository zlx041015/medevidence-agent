import json

from medevidence_agent.config import Settings
from medevidence_agent.llm import chat_completion
from medevidence_agent.models import ClinicalQuestion, SearchPlan


def build_rule_based_search_plan(question: ClinicalQuestion) -> SearchPlan:
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


def build_llm_search_plan(question: ClinicalQuestion, settings: Settings) -> SearchPlan:
    system_prompt = """
你是一个医学信息检索规划助手。你的任务不是回答医学问题，而是把用户问题转换成结构化检索计划。

请严格输出 JSON，不要输出任何额外解释。JSON 格式如下：
{
  "intent": "一句话描述检索目标",
  "keywords": ["关键词1", "关键词2", "关键词3"],
  "risk_level": "high"
}

要求：
1. 不要直接回答医学问题
2. keywords 应适合检索临床指南、综述或医学资料
3. risk_level 对治疗建议类问题统一输出 high
4. keywords 数量控制在 4 到 8 个之间
5. 关键词优先使用英文医学检索词
""".strip()

    user_prompt = f"用户问题：{question.text}"

    raw = chat_completion(
    settings=settings,
    system_prompt=system_prompt,
    user_prompt=user_prompt,
    temperature=0.2,
    )

    data = json.loads(raw)
    

    return SearchPlan(
        intent=data["intent"],
        keywords=data["keywords"],
        risk_level=data["risk_level"],
    )


def build_search_plan(question: ClinicalQuestion, settings: Settings) -> SearchPlan:
    try:
        return build_llm_search_plan(question, settings)
    except Exception as exc:
        print(f"[Planner fallback] LLM planner failed: {exc}")
        return build_rule_based_search_plan(question)