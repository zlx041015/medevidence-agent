import json

from medevidence_agent.config import Settings
from medevidence_agent.llm import chat_completion
from medevidence_agent.models import EvidenceItem, SourceDocument


def _pick_support_text(content: str) -> str:
    parts = [part.strip() for part in content.replace("\n", " ").split(".") if part.strip()]
    if not parts:
        return content[:180]
    return ". ".join(parts[:2]).strip()


def build_rule_based_claim_from_content(item: SourceDocument) -> str:
    content = item.content.lower()
    title = item.title.lower()
    combined = f"{title} {content}"

    if any(term in combined for term in ["hypertension", "blood pressure"]):
        if any(term in combined for term in ["ace inhibitor", "arb", "renin-angiotensin"]):
            return "该来源提示高血压管理重点在于规范降压治疗，并优先考虑与器官保护相关的治疗策略。"
        if any(term in combined for term in ["target", "individualized"]):
            return "该来源提示高血压管理需要结合个体风险设定控制目标，而不是采用完全固定的单一标准。"
        return "该来源提示高血压管理重点在于长期血压控制、风险评估和规范随访。"

    if any(term in combined for term in ["diabetes", "glycemic", "albuminuria", "proteinuria"]):
        if any(term in combined for term in ["screening", "retinal", "kidney", "monitoring"]):
            return "该来源提示糖尿病管理不仅关注血糖控制，也强调并发症筛查和长期监测。"
        return "该来源提示糖尿病管理重点在于代谢控制、并发症风险识别和长期综合管理。"

    if any(term in combined for term in ["chronic kidney disease", "ckd", "renal"]):
        return "该来源提示慢性肾病管理重点在于肾功能监测、风险分层和延缓疾病进展。"

    if any(term in combined for term in ["thyroid", "goiter", "hyperthyroidism", "hypothyroidism"]):
        if any(term in combined for term in ["compressive", "ultrasound", "surgical"]):
            return "该来源提示甲状腺疾病评估应结合压迫症状、功能状态和影像结果综合判断。"
        return "该来源提示甲状腺相关问题需要结合症状、功能和结构信息进行综合评估。"

    if any(term in combined for term in ["hyperlipidemia", "cholesterol", "ldl", "lipid"]):
        return "该来源提示高脂血症管理重点在于血脂控制、心血管风险评估和长期生活方式管理。"

    if any(term in combined for term in ["coronary artery disease", "secondary prevention", "cardiovascular"]):
        return "该来源提示冠心病管理重点在于二级预防、危险因素控制和长期随访。"

    if any(term in combined for term in ["heart failure", "decompensation", "cardiac function"]):
        return "该来源提示心力衰竭管理重点在于症状监测、功能评估和长期失代偿风险控制。"

    if any(term in combined for term in ["atrial fibrillation", "anticoagulation", "stroke risk"]):
        return "该来源提示房颤管理重点在于卒中风险评估、节律或频率控制以及长期抗凝决策。"

    if any(term in combined for term in ["stroke", "rehabilitation", "secondary prevention"]):
        return "该来源提示卒中后管理重点在于复发预防、危险因素控制和康复随访。"

    if any(term in combined for term in ["copd", "chronic obstructive pulmonary disease", "exacerbation"]):
        return "该来源提示慢阻肺稳定期管理重点在于加重风险评估、吸入治疗依从性和症状控制。"

    if any(term in combined for term in ["asthma", "inhaled therapy", "control"]):
        return "该来源提示哮喘长期管理重点在于控制水平评估、吸入治疗规范化和诱因管理。"

    if any(term in combined for term in ["pneumonia", "infection", "severity"]):
        return "该来源提示肺炎处理重点在于严重程度评估、感染控制和并发症监测。"

    if any(term in combined for term in ["tuberculosis", "tb"]):
        return "该来源提示结核管理重点在于规范治疗、感染控制和依从性随访。"

    if any(term in combined for term in ["anemia", "hemoglobin", "ferritin", "iron deficiency"]):
        return "该来源提示贫血评估重点在于明确病因、识别缺铁状态和监测血液学恢复。"

    if any(term in combined for term in ["osteoporosis", "fracture", "bone density"]):
        return "该来源提示骨质疏松管理重点在于骨折风险评估、骨健康管理和长期监测。"

    if any(term in combined for term in ["gout", "urate", "joint pain"]):
        return "该来源提示痛风管理重点在于尿酸控制、急性发作预防和复发风险管理。"

    if any(term in combined for term in ["rheumatoid arthritis", "joint inflammation"]):
        return "该来源提示类风湿关节炎管理重点在于炎症控制、关节功能保护和长期疗效监测。"

    if any(term in combined for term in ["osteoarthritis", "joint function"]):
        return "该来源提示骨关节炎管理重点在于疼痛控制、功能维持和保守治疗反应评估。"

    if any(term in combined for term in ["reflux", "gerd", "heartburn"]):
        return "该来源提示胃食管反流病管理重点在于症状控制、生活方式调整和警示症状识别。"

    if any(term in combined for term in ["peptic ulcer", "bleeding risk", "ulcer"]):
        return "该来源提示消化性溃疡处理重点在于症状评估、出血风险识别和复发预防。"

    if any(term in combined for term in ["gastroenteritis", "dehydration", "diarrhea"]):
        return "该来源提示急性胃肠炎处理重点在于脱水风险评估和支持治疗。"

    if any(term in combined for term in ["fatty liver", "metabolic risk", "liver"]):
        return "该来源提示脂肪肝管理重点在于代谢风险控制、生活方式干预和肝功能随访。"

    if any(term in combined for term in ["hepatitis b", "hbv"]):
        return "该来源提示慢性乙肝管理重点在于肝功能监测、疾病活动评估和长期风险分层。"

    if any(term in combined for term in ["urinary tract infection", "uti"]):
        return "该来源提示尿路感染评估重点在于症状判断、复发风险识别和规范处理。"

    if any(term in combined for term in ["prostatic hyperplasia", "bph", "urinary symptoms"]):
        return "该来源提示前列腺增生管理重点在于排尿症状评估、生活质量影响和长期随访。"

    if any(term in combined for term in ["kidney stone", "renal stone", "stone recurrence"]):
        return "该来源提示肾结石管理重点在于疼痛评估、复发风险控制和后续预防。"

    if any(term in combined for term in ["depression", "mood symptoms", "relapse"]):
        return "该来源提示抑郁症管理重点在于症状严重度评估、复发风险监测和长期治疗依从性。"

    if any(term in combined for term in ["anxiety", "trigger", "functional impact"]):
        return "该来源提示焦虑障碍管理重点在于症状控制、诱因识别和功能恢复评估。"

    if any(term in combined for term in ["insomnia", "sleep hygiene", "sleep"]):
        return "该来源提示失眠管理重点在于睡眠习惯评估、症状持续性判断和行为管理。"

    if any(term in combined for term in ["migraine", "headache", "trigger"]):
        return "该来源提示偏头痛管理重点在于发作负担评估、诱因识别和长期症状随访。"

    if any(term in combined for term in ["eczema", "itch", "skin barrier"]):
        return "该来源提示湿疹管理重点在于皮肤屏障保护、瘙痒控制和诱因管理。"

    if any(term in combined for term in ["urticaria", "allergy", "wheal"]):
        return "该来源提示荨麻疹管理重点在于症状负担评估、可能诱因识别和反复发作监测。"

    if any(term in combined for term in ["acne", "skin care", "comedone"]):
        return "该来源提示痤疮管理重点在于皮损严重度评估、规范治疗和复发管理。"

    if any(term in combined for term in ["obesity", "weight management", "metabolic risk"]):
        return "该来源提示肥胖症管理重点在于体重控制、代谢风险评估和长期生活方式干预。"

    return "该来源提示当前问题的管理需要基于症状、风险因素和随访信息进行综合判断。"


def extract_evidence_rule_based(candidates: list[SourceDocument]) -> list[EvidenceItem]:
    evidence = []

    for item in candidates:
        claim = build_rule_based_claim_from_content(item)
        support_text = _pick_support_text(item.content)

        evidence.append(
            EvidenceItem(
                source_id=item.source_id,
                title=item.title,
                claim=claim,
                support_text=support_text,
                source_type=item.source_type,
                year=item.year,
                url=item.url,
                score=item.relevance_score,
            )
        )

    return evidence


def extract_single_evidence_with_llm(item: SourceDocument, settings: Settings) -> EvidenceItem:
    system_prompt = """
你是一个医学证据抽取助手。你的任务不是回答问题，而是从单条来源内容中提取结构化证据。
请严格输出 JSON，不要输出任何额外解释。JSON 格式如下：
{
  "claim": "一句中文结论，概括该来源支持的核心观点",
  "support_text": "从原文中摘取最能支持 claim 的一两句内容"
}

要求：
1. claim 用中文表达
2. claim 应尽量简洁、客观，不要夸大
3. support_text 必须来自原始内容，不要编造
4. 不要输出 markdown，不要输出代码块
""".strip()

    user_prompt = f"""来源标题：{item.title}
来源类型：{item.source_type}
年份：{item.year}
原始内容：{item.content}
"""

    raw = chat_completion(
        settings=settings,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        temperature=0.2,
    )

    data = json.loads(raw)

    return EvidenceItem(
        source_id=item.source_id,
        title=item.title,
        claim=data["claim"],
        support_text=data["support_text"],
        source_type=item.source_type,
        year=item.year,
        url=item.url,
        score=item.relevance_score,
    )


def extract_evidence(candidates: list[SourceDocument], settings: Settings) -> list[EvidenceItem]:
    try:
        return [extract_single_evidence_with_llm(item, settings) for item in candidates]
    except Exception as exc:
        print(f"[Extractor fallback] LLM extractor failed: {exc}")
        return extract_evidence_rule_based(candidates)


def extract_evidence_with_mode(
    candidates: list[SourceDocument],
    settings: Settings,
    mode: str = "auto",
) -> list[EvidenceItem]:
    if mode == "rule":
        return extract_evidence_rule_based(candidates)
    return extract_evidence(candidates, settings)
