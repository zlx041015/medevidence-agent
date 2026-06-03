import json

from medevidence_agent.config import Settings
from medevidence_agent.llm import chat_completion
from medevidence_agent.models import ClinicalQuestion, SearchPlan


def build_rule_based_search_plan(question: ClinicalQuestion) -> SearchPlan:
    text = question.text.strip()
    lowered = text.lower()

    keywords = ["clinical guideline"]

    disease_rules = [
        (["糖尿病", "diabetes"], ["diabetes mellitus"]),
        (["高血压", "hypertension"], ["hypertension", "blood pressure"]),
        (["蛋白尿", "白蛋白尿", "albuminuria", "proteinuria"], ["proteinuria", "albuminuria"]),
        (["慢性肾病", "肾病", "chronic kidney disease", "ckd"], ["chronic kidney disease"]),
        (["甲状腺", "thyroid"], ["thyroid"]),
        (["甲状腺肿大", "goiter", "thyroid enlargement"], ["goiter", "thyroid enlargement"]),
        (["高脂血症", "血脂", "hyperlipidemia", "cholesterol", "ldl"], ["hyperlipidemia", "ldl cholesterol"]),
        (["冠心病", "心绞痛", "coronary", "cad"], ["coronary artery disease", "secondary prevention"]),
        (["心力衰竭", "heart failure"], ["heart failure", "cardiac function"]),
        (["房颤", "atrial fibrillation", "af"], ["atrial fibrillation", "stroke risk"]),
        (["脑卒中", "stroke"], ["stroke", "secondary prevention", "rehabilitation"]),
        (["慢阻肺", "copd"], ["copd", "stable management", "exacerbation risk"]),
        (["哮喘", "asthma"], ["asthma", "control", "inhaled therapy"]),
        (["肺炎", "community acquired pneumonia", "cap"], ["community acquired pneumonia", "severity"]),
        (["肺结核", "tuberculosis", "tb"], ["tuberculosis", "infection control"]),
        (["贫血", "anemia", "缺铁"], ["iron deficiency anemia", "hemoglobin", "ferritin"]),
        (["骨质疏松", "osteoporosis"], ["osteoporosis", "fracture risk"]),
        (["痛风", "gout"], ["gout", "urate", "joint pain"]),
        (["类风湿", "rheumatoid arthritis", "ra"], ["rheumatoid arthritis", "joint inflammation"]),
        (["骨关节炎", "osteoarthritis"], ["osteoarthritis", "joint pain", "function"]),
        (["胃食管反流", "gerd", "reflux"], ["gastroesophageal reflux", "heartburn"]),
        (["消化性溃疡", "ulcer"], ["peptic ulcer", "bleeding risk"]),
        (["胃肠炎", "gastroenteritis"], ["gastroenteritis", "dehydration"]),
        (["脂肪肝", "fatty liver"], ["fatty liver", "metabolic risk"]),
        (["乙肝", "hepatitis b", "hbv"], ["hepatitis b", "liver function"]),
        (["尿路感染", "urinary tract infection", "uti"], ["urinary tract infection", "infection"]),
        (["前列腺增生", "bph", "benign prostatic hyperplasia"], ["benign prostatic hyperplasia", "urinary symptoms"]),
        (["肾结石", "kidney stone", "stone"], ["kidney stone", "recurrence risk"]),
        (["抑郁", "depression"], ["depression", "mood symptoms"]),
        (["焦虑", "anxiety"], ["anxiety disorder", "symptom control"]),
        (["失眠", "insomnia"], ["insomnia", "sleep hygiene"]),
        (["偏头痛", "migraine"], ["migraine", "headache", "trigger"]),
        (["湿疹", "eczema"], ["eczema", "itch", "skin barrier"]),
        (["荨麻疹", "urticaria"], ["urticaria", "allergy", "itch"]),
        (["痤疮", "acne"], ["acne", "skin care"]),
        (["肥胖", "obesity"], ["obesity", "weight management", "metabolic risk"]),
    ]

    modifier_rules = [
        (["并发症", "complication"], ["complications"]),
        (["筛查", "screening", "monitoring"], ["screening", "monitoring"]),
        (["治疗", "therapy", "treatment"], ["treatment", "drug therapy"]),
        (["一线", "首选", "first-line"], ["first-line"]),
        (["目标", "target"], ["management target", "individualized treatment"]),
        (["风险", "risk"], ["risk stratification"]),
        (["随访", "follow-up", "follow up"], ["follow-up", "long-term management"]),
        (["指南", "guideline"], ["guideline"]),
        (["压迫", "compressive"], ["compressive symptoms"]),
        (["康复", "rehabilitation"], ["rehabilitation"]),
    ]

    for triggers, additions in disease_rules + modifier_rules:
        if any(trigger in text or trigger in lowered for trigger in triggers):
            keywords.extend(additions)

    keywords = list(dict.fromkeys(keywords))

    return SearchPlan(
        intent=f"Find evidence-based management suggestions for: {question.text}",
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
3. 治疗、并发症、风险管理类问题可标为 high
4. keywords 数量控制在 4 到 8 个之间
5. 优先使用英文医学检索词
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
