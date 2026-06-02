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

## Experiment 17: First Real Source Retrieval via PubMed ESearch
- Change:
  - 新增 `src/medevidence_agent/tools/pubmed.py`
  - 实现 `search_pubmed_pmids()`，使用 PubMed E-utilities 的 `esearch.fcgi` 获取 PMID 列表
- Observations:
  - 使用检索词 `diabetes mellitus proteinuria hypertension ACE inhibitor` 成功返回真实 PMID 列表
  - 说明 PubMed 检索接口可访问，且当前项目已具备真实医学来源入口
- Insight:
  - v0.3 的第一步应先解决“如何获取真实来源”，而不是一开始就做全文解析
  - 通过 `PubMed -> PMID` 这一步，系统已经从 mock 数据阶段进入真实来源接入阶段

## Experiment 18: Map PubMed Results into SourceDocument
- Change:
  - 在 `pubmed.py` 中新增 `fetch_pubmed_articles()`
  - 使用 PubMed `efetch.fcgi` 获取标题、摘要和年份
  - 将真实文献结果映射为项目内部的 `SourceDocument`
- Observations:
  - 系统已能将真实 PubMed 文献转换为 `SourceDocument`
  - 每条来源包含 PMID、标题、年份、PubMed URL 和摘要拼接内容
  - 真实检索结果会带来更复杂的来源分布，例如优先返回与蛋白尿/肾病相关的药物研究，而不一定直接是指南型结论
- Insight:
  - 当前项目已具备从真实医学来源构建证据输入的能力
  - 与 mock 数据不同，真实来源引入后，Planner 和 Retriever 的检索质量将直接影响后续证据链质量

## Experiment 19: First End-to-End Run with Real PubMed Sources
- Change:
  - 在 `workflow.py` 中加入 `source_mode` 分支
  - 当 `MEDEVIDENCE_SOURCE_MODE=pubmed` 时，使用 `PubMed -> PMID -> SourceDocument` 替代本地 mock 数据
- Observations:
  - 系统成功完成了从真实 PubMed 检索到最终中文结论生成的端到端流程
  - Retriever 返回了真实文献来源，而不再依赖 `mock_sources.json`
  - LLM Extractor 能对真实文献摘要抽取中文 claim
  - 在当前测试问题下，PubMed 检索结果偏向单药研究（如 irbesartan），而不是理想中的指南型证据
  - Verifier 因证据不足、来源不够权威而显著降低 confidence，并触发人工审核
- Insight:
  - v0.3 的核心问题已经从“系统是否能跑通”转向“真实来源检索质量是否足够好”
  - 对真实医学来源而言，Planner 的检索词设计和来源过滤策略将直接决定系统最终结论质量

## Experiment 20: Domain Mismatch Under Planner Fallback
- Question:
  - 胰腺癌应该怎样用药
- Observations:
  - 在 LLM Planner 失败时，旧版规则 fallback 会错误地退回糖尿病/高血压主题
  - 这会导致非目标疾病问题被错误检索到糖尿病/高血压相关文献
- Insight:
  - Agent 系统中的 fallback 不能只是“旧逻辑继续跑”，而必须与用户当前问题主题保持一致
  - 规则版 Planner 需要从特定场景硬编码，升级为通用医学问题回退机制

## Experiment 21: Generic Fallback Planner Prevents Topic Drift
- Question:
  - 胰腺癌应该怎样用药
- Observations:
  - 即使 LLM Planner 调用失败，通用规则版 fallback 仍能围绕 `cancer`、`pancreatic cancer`、`drug therapy` 等关键词继续检索
  - 检索结果开始出现胰腺癌指南、癌症相关治疗和肿瘤风险管理相关文献，不再跑偏到糖尿病/高血压主题
  - 当前 Verifier 仍因其规则围绕 ACEI/ARB 设计而给出较低置信度和冲突提示
- Insight:
  - Fallback planner 的通用化已经解决了“主题跑偏”的核心问题
  - 下一阶段需要继续把下游核验逻辑从糖尿病高血压专用规则，升级为面向更广泛疾病问题的通用核验框架

## Experiment 22: Shift to PubMed Direct-Through Workflow
- Change:
  - 将 `workflow.py` 调整为 `source_mode=pubmed` 时直接使用 PubMed 检索与抓取结果
  - 弱化对本地 mock 来源库和强规则重排的依赖
  - 将 `Verifier` 重构为面向多疾病问题的轻量审核器，不再绑定 ACEI/ARB 场景
- Observations:
  - 工作流已可实现“问题 -> PubMed 检索 -> LLM 抽取 -> LLM 总结”的直通式链路
  - 对非糖尿病高血压场景，系统不再因旧 Verifier 规则而明显误判
- Insight:
  - 对当前项目而言，实时检索 + 抽取 + 总结比自建本地数据库更适合作为可展示、可落地的 agent 路线
  - 将复杂规则简化为轻量审核，更有利于提升通用性

## Experiment 23: Thyroid Goiter Complications End-to-End Test
- Question:
  - 甲状腺肿大会有什么并发症
- Observations:
  - LLM Planner 成功生成了与 `goiter`、`thyroid enlargement`、`complications`、`compressive symptoms`、`hyperthyroidism`、`hypothyroidism` 相关的检索词
  - PubMed 直通检索返回了与甲状腺肿大并发症、压迫症状和功能异常相关的真实来源
  - LLM Extractor 能从病例报告、病例系列和手术相关文献中提炼出并发症与风险信息
  - LLM Writer 能围绕“并发症与风险识别”生成较自然的中文总结
  - 当前来源的 `score` 仍然显示为 `0.0`，说明 PubMed 直通模式下还没有补充轻量相关性评分
- Insight:
  - 直通式工作流已经能够处理通用医学问题，而不局限于原始糖尿病高血压场景
  - 下一步应补充轻量相关性评分或来源优先级逻辑，以提升置信度计算的可解释性

## Experiment 17: First Real Source Retrieval via PubMed ESearch
- Change:
  - 新增 `src/medevidence_agent/tools/pubmed.py`
  - 实现 `search_pubmed_pmids()`，使用 PubMed E-utilities 的 `esearch.fcgi` 获取 PMID 列表
- Observations:
  - 使用检索词 `diabetes mellitus proteinuria hypertension ACE inhibitor` 成功返回真实 PMID 列表
  - 说明 PubMed 检索接口可访问，且当前项目已具备真实医学来源入口
- Insight:
  - v0.3 的第一步应先解决“如何获取真实来源”，而不是一开始就做全文解析
  - 通过 `PubMed -> PMID` 这一步，系统已经从 mock 数据阶段进入真实来源接入阶段

## Experiment 18: Map PubMed Results into SourceDocument
- Change:
  - 在 `pubmed.py` 中新增 `fetch_pubmed_articles()`
  - 使用 PubMed `efetch.fcgi` 获取标题、摘要和年份
  - 将真实文献结果映射为项目内部的 `SourceDocument`
- Observations:
  - 系统已能将真实 PubMed 文献转换为 `SourceDocument`
  - 每条来源包含 PMID、标题、年份、PubMed URL 和摘要拼接内容
  - 真实检索结果会带来更复杂的来源分布，例如优先返回与蛋白尿/肾病相关的药物研究，而不一定直接是指南型结论
- Insight:
  - 当前项目已具备从真实医学来源构建证据输入的能力
  - 与 mock 数据不同，真实来源引入后，Planner 和 Retriever 的检索质量将直接影响后续证据链质量
