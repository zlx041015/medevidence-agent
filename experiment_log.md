# MedEvidence Agent Experiment Log

## Experiment 1: Baseline Run
- Question: 2型糖尿病合并高血压患者的一线治疗建议是什么？
- Settings:
  - top_k = 3
  - evidence_score_threshold = 0.55
  - confidence_threshold = 0.70
- Observations:
  - Planner 能正确生成与糖尿病、高血压、一线治疗相关的关键词
  - Retriever 能筛出 guideline 和 review，并过滤低质量 blog
  - Verifier 给出中等偏上的 confidence
  - Writer 能输出带引用的初步结论

## Experiment 2: Increase Confidence Threshold
- Change:
  - confidence_threshold: 0.70 -> 0.75
- Observations:
  - 在证据不变的情况下，系统变得更谨慎
  - 原本可直接输出的结果，变成需要人工审核
- Insight:
  - confidence_threshold 控制的是系统放行标准，不是证据本身质量

## Experiment 3: Increase Evidence Score Threshold
- Change:
  - evidence_score_threshold: 0.55 -> 0.75
- Observations:
  - 进入候选来源的数量减少
  - 证据池更干净，但可能损失信息覆盖
- Insight:
  - 证据过滤阈值需要在“减少噪声”和“保留足够证据”之间平衡

## Experiment 4: Adjust top_k
- Change:
  - top_k: 3 -> 1
  - top_k: 3 -> 4
- Observations:
  - top_k = 1 时，只保留单一高分来源，confidence 下降
  - top_k = 4 时，多来源支持更充分，但仍受其他阈值约束
- Insight:
  - 单一高质量来源不一定优于多来源交叉支持
  - top_k 需要在证据丰富度和噪声控制之间平衡

## Experiment 5: Upgrade Extractor
- Change:
  - 从固定 claim 改为基于内容的规则抽取
- Observations:
  - 不同来源开始产生不同 claim
  - 系统输出更贴近各来源的内容重点
- Insight:
  - Extractor 的作用不只是转格式，还影响后续核验质量

## Experiment 6: Upgrade Verifier
- Change:
  - 除平均分和 guideline 数量外，加入对 claim 内容的判断
- Observations:
  - 系统能识别 ACEI/ARB、生活方式干预、个体化目标等支持点
  - summary_claim 开始根据证据动态生成
- Insight:
  - 核验不应只看“有多少证据”，还应看“证据支持了什么”

## Experiment 7: Upgrade Planner
- Change:
  - 根据问题中的临床要点动态扩展关键词
- Observations:
  - 不同问题会生成不同的关键词组合
  - Planner 对蛋白尿、肾病、目标管理等概念更敏感
- Insight:
  - 检索质量不仅取决于资料库，还取决于问题规划是否合理

## Experiment 8: Multi-Question Stability Test
- Questions:
  - 2型糖尿病合并高血压患者的一线治疗建议是什么？
  - 糖尿病伴蛋白尿时高血压首选什么药？
  - 糖尿病患者的血压控制目标应该如何制定？
- Observations:
  - Planner 已能根据问题内容动态调整关键词
  - 蛋白尿问题中新增了 `albuminuria`
  - 血压目标问题中新增了 `blood pressure targets` 和 `individualized targets`
  - Retriever 的来源排序和分数会随问题变化而变化
  - 系统对治疗建议类问题表现较自然
  - 对血压目标制定类问题，最终总结仍偏向药物选择和生活方式干预，尚未充分体现目标管理和个体化控制
- Insight:
  - 当前系统已具备基础问题分化能力，但下游 Extractor 和 Verifier 仍偏向“治疗建议模板”
  - 下一步应增强对 `individualized targets`、`blood pressure targets` 等内容的抽取和核验能力