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

## Experiment 9: Archive v0.1 Baseline Workflow
- Change:
  - 初始化本地 git 仓库
  - 添加 `.gitignore`
  - 提交当前版本为 `v0.1 baseline workflow`
  - 创建 GitHub 仓库并完成首次推送
- Observations:
  - 当前项目已形成稳定的 baseline workflow 版本
  - 远端推送过程中，最初 git HTTPS 连接失败
  - 通过将 git 的 SSL backend 切换为 `schannel` 后，成功完成推送
- Insight:
  - 项目版本管理是 AI 应用工程的重要组成部分，不只是代码能跑，还要能归档、回退和协作
  - Windows 环境下 git 的 HTTPS/TLS 链路可能与默认 SSL backend 有兼容性问题，必要时可切换为 `schannel`

## Experiment 10: First LLM Planner Integration
- Change:
  - 新增 `llm.py` 作为统一模型调用层
  - 将 Planner 改为优先调用 LLM，失败时回退到规则版 Planner
- Observations:
  - LLM Planner 已经能够被工作流真正调用
  - 当前第三方兼容接口返回内容未能直接被 `json.loads()` 解析
  - fallback 机制成功生效，系统未中断，仍然完成了后续检索、抽取、核验和写作流程
- Insight:
  - 当前问题不在于工作流接入失败，而在于第三方 LLM 返回格式与预期 JSON 不完全一致
  - 下一步需要先查看原始返回内容，再决定是加强 prompt、清洗 markdown，还是适配中转接口返回结构

## Experiment 11: LLM Planner Failure Localization
- Change:
  - 在 Planner 中增加 LLM fallback 调试
  - 尝试运行 LLM Planner 节点
- Observations:
  - LLM Planner 未成功返回可解析的检索计划
  - fallback 机制自动切回规则版 Planner，整个工作流未中断
  - 由于 `planner.py` 中的原始输出打印未触发，说明异常更早发生在 `llm.py` 内部 JSON 解析阶段
- Insight:
  - 当前问题已定位到第三方兼容接口的原始 HTTP 响应解析，而不是 Planner 节点逻辑本身
  - 下一步应直接检查 `llm.py` 接收到的原始响应内容，以判断是空响应、错误 JSON 还是非标准兼容格式

## Experiment 12: Third-Party LLM Endpoint Diagnosis
- Change:
  - 在 `llm.py` 中打印原始 HTTP 响应内容，排查 LLM Planner 失败原因
- Observations:
  - 原始响应返回的是完整 HTML 页面，而不是 OpenAI 兼容的 JSON 响应
  - 页面标题显示为 `Link API - AI API Gateway`
  - 说明当前 `.env` 中配置的 `OPENAI_BASE_URL` 实际上是站点前端页面地址，而不是真正的 API Base URL
- Insight:
  - 当前问题不在于 prompt 或 JSON 解析逻辑，而在于请求被发送到了错误的接口地址
  - 下一步应从中转站文档或示例代码中找到正确的 OpenAI 兼容 API Base URL

## Experiment 13: LLM Planner Successfully Activated
- Change:
  - 修正第三方中转站的 `OPENAI_BASE_URL`
  - 将 Planner 升级为优先调用 LLM，失败时回退规则版
- Observations:
  - LLM 返回了标准 OpenAI 兼容 JSON 响应
  - Planner 成功输出结构化检索计划，无需 fallback
  - 生成的关键词比规则版更自然，且更贴近医学检索表达，例如 `diabetes mellitus`、`proteinuria`、`first-line antihypertensive`
  - 下游 Retriever 结果随 LLM Planner 输出发生变化，仅保留了更相关的 guideline 来源
- Insight:
  - 当前项目已经具备了第一个真正由 LLM 驱动的 agent 节点
  - Planner 的语义理解能力会直接影响后续检索结果，因此这是从 workflow baseline 走向 agent 系统的关键一步

## Experiment 14: Remove Temporary Planner Debug Logs
- Change:
  - 删除 `llm.py` 和 `planner.py` 中用于排查接口问题的原始响应打印
  - 保留 Planner fallback 提示，作为运行期异常的最小可观测性
- Observations:
  - 正常运行输出变得更干净，便于观察工作流本身的行为
  - LLM Planner 仍可正常工作，说明调试输出删除后没有影响主流程
- Insight:
  - 调试日志在排查阶段很有价值，但在主流程稳定后应及时收口
  - 保留最小失败提示、移除冗余原始响应输出，是更适合持续开发的状态

## Experiment 15: LLM Extractor Successfully Activated
- Change:
  - 将 Extractor 升级为优先调用 LLM，失败时回退规则版抽取
  - 在工作流中为 Extractor 显式传入 `settings`
- Observations:
  - Extractor 成功输出了由模型生成的中文 claim，没有触发 fallback
  - 相比规则版，claim 更贴近原始来源内容，并明确体现了“蛋白尿/慢性肾病时 ACEI/ARB 更常被推荐”这一细节
  - 在当前问题下，Retriever 仅保留了 ADA 2024 这一条更相关的 guideline 来源
  - 由于证据来源数量减少，Verifier 给出的 confidence 降至 0.518，系统继续保持人工审核标记
- Insight:
  - LLM Extractor 已经成为第二个真正参与主流程的 agent 节点
  - 更精准的抽取不等于更高的最终置信度，证据数量、来源多样性和核验规则仍然会共同影响系统判断

## Experiment 16: LLM Writer Successfully Activated
- Change:
  - 将 Writer 升级为优先调用 LLM，失败时回退规则版输出
  - 在工作流中为 Writer 显式传入 `settings`
- Observations:
  - Writer 成功生成了更自然、更完整的中文医学证据总结，没有触发 fallback
  - 相比规则版模板，LLM Writer 能更好地整合个体化血压目标、白蛋白尿/慢性肾病背景以及人工审核提示
  - 最终输出的可读性明显提升，更接近真实医学信息助手的表达方式
- Insight:
  - 在 Verifier 仍然作为规则安全闸门的情况下，LLM Writer 是一种低风险、高收益的升级
  - 当前系统已经具备“LLM 负责理解与表达，规则负责检索排序和安全把关”的 v0.2 核心形态
