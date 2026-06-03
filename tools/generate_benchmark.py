import json
from pathlib import Path


TOPICS = [
    {
        "name": "高血压",
        "keywords": ["hypertension", "blood pressure", "management", "target"],
        "sources": ["guideline_esh_2023", "guideline_ada_bp_targets_2024"],
        "risk": "high",
    },
    {
        "name": "2型糖尿病",
        "keywords": ["diabetes mellitus", "glycemic control", "complication", "management"],
        "sources": ["guideline_ada_2024", "knowledgebase_screening_2023"],
        "risk": "high",
    },
    {
        "name": "慢性肾病",
        "keywords": ["chronic kidney disease", "albuminuria", "monitoring", "management"],
        "sources": ["guideline_nice_ckd_2021", "guideline_ada_bp_targets_2024"],
        "risk": "high",
    },
    {
        "name": "甲状腺肿大",
        "keywords": ["thyroid", "goiter", "compressive symptoms", "management"],
        "sources": ["consensus_thyroid_2022"],
        "risk": "high",
    },
    {
        "name": "高脂血症",
        "keywords": ["hyperlipidemia", "ldl cholesterol", "cardiovascular risk", "management"],
        "sources": ["guideline_lipid_2023", "review_lipid_primarycare_2022"],
        "risk": "medium",
    },
    {
        "name": "冠心病",
        "keywords": ["coronary artery disease", "secondary prevention", "cardiovascular risk", "therapy"],
        "sources": ["guideline_cad_secondary_2023", "review_secondary_prevention_2022"],
        "risk": "high",
    },
    {
        "name": "心力衰竭",
        "keywords": ["heart failure", "cardiac function", "follow-up", "therapy"],
        "sources": ["guideline_heart_failure_2023", "review_heart_failure_2022"],
        "risk": "high",
    },
    {
        "name": "房颤",
        "keywords": ["atrial fibrillation", "stroke risk", "anticoagulation", "management"],
        "sources": ["guideline_af_2023", "review_af_2022"],
        "risk": "high",
    },
    {
        "name": "脑卒中后管理",
        "keywords": ["stroke", "secondary prevention", "rehabilitation", "risk"],
        "sources": ["guideline_stroke_2023", "review_stroke_2022"],
        "risk": "high",
    },
    {
        "name": "慢阻肺稳定期",
        "keywords": ["copd", "stable management", "exacerbation risk", "therapy"],
        "sources": ["guideline_copd_2024", "review_copd_primarycare_2022"],
        "risk": "medium",
    },
    {
        "name": "支气管哮喘",
        "keywords": ["asthma", "control", "inhaled therapy", "follow-up"],
        "sources": ["guideline_asthma_2024", "review_asthma_management_2022"],
        "risk": "medium",
    },
    {
        "name": "社区获得性肺炎",
        "keywords": ["community acquired pneumonia", "severity", "infection", "therapy"],
        "sources": ["guideline_cap_2023", "review_pneumonia_2022"],
        "risk": "high",
    },
    {
        "name": "肺结核",
        "keywords": ["tuberculosis", "infection", "follow-up", "screening"],
        "sources": ["guideline_tb_2023", "review_tb_2022"],
        "risk": "high",
    },
    {
        "name": "缺铁性贫血",
        "keywords": ["iron deficiency anemia", "hemoglobin", "evaluation", "management"],
        "sources": ["guideline_anemia_2023", "review_iron_deficiency_2022"],
        "risk": "medium",
    },
    {
        "name": "骨质疏松",
        "keywords": ["osteoporosis", "fracture risk", "screening", "management"],
        "sources": ["guideline_osteoporosis_2023", "review_osteoporosis_2022"],
        "risk": "medium",
    },
    {
        "name": "痛风",
        "keywords": ["gout", "urate", "joint pain", "management"],
        "sources": ["guideline_gout_2023", "review_gout_2022"],
        "risk": "medium",
    },
    {
        "name": "类风湿关节炎",
        "keywords": ["rheumatoid arthritis", "joint inflammation", "therapy", "follow-up"],
        "sources": ["guideline_ra_2023", "review_ra_2022"],
        "risk": "high",
    },
    {
        "name": "骨关节炎",
        "keywords": ["osteoarthritis", "joint pain", "function", "management"],
        "sources": ["guideline_oa_2023", "review_oa_2022"],
        "risk": "medium",
    },
    {
        "name": "胃食管反流病",
        "keywords": ["gastroesophageal reflux", "heartburn", "therapy", "lifestyle"],
        "sources": ["guideline_gerd_2023", "review_gerd_2022"],
        "risk": "medium",
    },
    {
        "name": "消化性溃疡",
        "keywords": ["peptic ulcer", "bleeding risk", "therapy", "evaluation"],
        "sources": ["guideline_ulcer_2023", "review_ulcer_2022"],
        "risk": "high",
    },
    {
        "name": "急性胃肠炎",
        "keywords": ["gastroenteritis", "dehydration", "infection", "management"],
        "sources": ["guideline_gastroenteritis_2023", "review_gastroenteritis_2022"],
        "risk": "medium",
    },
    {
        "name": "脂肪肝",
        "keywords": ["fatty liver", "metabolic risk", "lifestyle", "monitoring"],
        "sources": ["guideline_fatty_liver_2023", "review_fatty_liver_2022"],
        "risk": "medium",
    },
    {
        "name": "乙肝慢性感染",
        "keywords": ["hepatitis b", "liver function", "monitoring", "therapy"],
        "sources": ["guideline_hbv_2023", "review_hbv_2022"],
        "risk": "high",
    },
    {
        "name": "尿路感染",
        "keywords": ["urinary tract infection", "infection", "antibiotic therapy", "evaluation"],
        "sources": ["guideline_uti_2023", "review_uti_2022"],
        "risk": "medium",
    },
    {
        "name": "良性前列腺增生",
        "keywords": ["benign prostatic hyperplasia", "urinary symptoms", "management", "follow-up"],
        "sources": ["guideline_bph_2023", "review_bph_2022"],
        "risk": "medium",
    },
    {
        "name": "肾结石",
        "keywords": ["kidney stone", "pain", "evaluation", "recurrence risk"],
        "sources": ["guideline_stone_2023", "review_stone_2022"],
        "risk": "medium",
    },
    {
        "name": "抑郁症",
        "keywords": ["depression", "mood symptoms", "follow-up", "therapy"],
        "sources": ["guideline_depression_2023", "review_depression_2022"],
        "risk": "high",
    },
    {
        "name": "焦虑障碍",
        "keywords": ["anxiety disorder", "symptom control", "therapy", "follow-up"],
        "sources": ["guideline_anxiety_2023", "review_anxiety_2022"],
        "risk": "medium",
    },
    {
        "name": "失眠",
        "keywords": ["insomnia", "sleep hygiene", "therapy", "follow-up"],
        "sources": ["guideline_insomnia_2023", "review_insomnia_2022"],
        "risk": "medium",
    },
    {
        "name": "偏头痛",
        "keywords": ["migraine", "headache", "trigger", "management"],
        "sources": ["guideline_migraine_2023", "review_migraine_2022"],
        "risk": "medium",
    },
    {
        "name": "湿疹",
        "keywords": ["eczema", "skin barrier", "itch", "management"],
        "sources": ["guideline_eczema_2023", "review_eczema_2022"],
        "risk": "medium",
    },
    {
        "name": "荨麻疹",
        "keywords": ["urticaria", "allergy", "itch", "management"],
        "sources": ["guideline_urticaria_2023", "review_urticaria_2022"],
        "risk": "medium",
    },
    {
        "name": "痤疮",
        "keywords": ["acne", "skin care", "therapy", "follow-up"],
        "sources": ["guideline_acne_2023", "review_acne_2022"],
        "risk": "medium",
    },
    {
        "name": "肥胖症",
        "keywords": ["obesity", "weight management", "lifestyle", "metabolic risk"],
        "sources": ["guideline_obesity_2023", "review_obesity_2022"],
        "risk": "high",
    },
]

PATTERNS = [
    ("一线管理或治疗的核心是什么？", "treatment", "该病症管理通常强调规范化治疗、风险控制和个体化决策。"),
    ("为什么需要重视相关筛查或评估？", "screening", "相关筛查和评估有助于更早识别风险、并发症或病情严重程度。"),
    ("长期随访时最重要的关注点是什么？", "follow_up", "长期随访重点通常在症状变化、风险趋势、依从性和治疗效果评估。"),
    ("从风险控制角度看，为什么需要个体化处理？", "risk_management", "风险控制常需要结合病情严重度、共病、年龄和长期预后进行个体化处理。"),
]

SUFFIXES = [
    "请结合循证医学角度说明。",
    "如果用于门诊随访，重点应如何理解？",
    "如果强调长期管理，这个问题应如何把握？",
    "从患者教育角度看，最重要的提示是什么？",
    "如果用于风险分层，应优先关注哪些信息？",
]


def build_question(topic_name: str, pattern: str, suffix: str) -> str:
    return f"{topic_name}{pattern.rstrip('？')}，{suffix}"


def main() -> None:
    items = []
    for idx in range(100):
        topic = TOPICS[idx % len(TOPICS)]
        pattern, qtype, claim = PATTERNS[(idx // len(TOPICS)) % len(PATTERNS)]
        suffix = SUFFIXES[(idx // (len(TOPICS) * len(PATTERNS))) % len(SUFFIXES)]
        items.append(
            {
                "question_id": f"q{idx + 1}",
                "question": build_question(topic["name"], pattern, suffix),
                "question_type": qtype,
                "risk_level": topic["risk"],
                "gold_keywords": topic["keywords"],
                "gold_sources": topic["sources"],
                "gold_claim": claim,
                "needs_human_review": topic["risk"] == "high",
            }
        )

    Path("data/benchmark_questions.json").write_text(
        json.dumps(items, ensure_ascii=False, indent=2),
        encoding="utf-8-sig",
    )


if __name__ == "__main__":
    main()
