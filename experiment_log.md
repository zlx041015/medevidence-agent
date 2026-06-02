# MedEvidence Agent Experiment Log

## Experiment 1: Baseline Rule Workflow
- Goal:
  - 从 0 到 1 搭建一个可运行的医学证据工作流骨架
- Changes:
  - 建立 `Planner -> Retriever -> Extractor -> Verifier -> Writer` 基础链路
  - 使用本地 `mock_sources.json` 作为来源
- Observations:
  - 系统可以完成单问题输入、来源筛选、规则抽取和结果输出
  - 结构清晰，但仍依赖手写规则和 mock 数据
- Insight:
  - 先搭工作流骨架再逐步引入 LLM 和真实来源，是更稳妥的工程路线

## Experiment 2: Threshold and Top-K Tuning
- Goal:
  - 验证 `confidence_threshold`、`evidence_score_threshold`、`top_k` 对结果的影响
- Changes:
  - 分别调高/调低审核阈值、来源过滤阈值和候选来源数量
- Observations:
  - 审核阈值决定系统是否放行，而不改变证据本身
  - 过滤阈值过高会丢信息，过低会引入噪声
  - `top_k` 太小会导致证据单薄，太大则会带入噪声
- Insight:
  - 证据系统优化的核心是权衡召回率、精确率和审核严格度

## Experiment 3: Rule-Based Extractor and Verifier Upgrade
- Goal:
  - 让系统不再只输出固定模板，而是开始体现来源内容差异
- Changes:
  - Extractor 从固定 claim 升级为基于来源内容的规则抽取
  - Verifier 开始根据 claim 内容而不是纯数量进行判断
- Observations:
  - 不同来源开始对应不同 claim
  - 系统对 `ACEI/ARB`、生活方式和个体化目标等信息的区分更清晰
- Insight:
  - 即使是规则版系统，只要拆成节点并让中间表示更结构化，也能获得明显增益

## Experiment 4: Planner Rule Generalization
- Goal:
  - 让规则版 Planner 不只支持糖尿病/高血压一个主题
- Changes:
  - 为 Planner 添加更通用的关键词扩展逻辑
  - 覆盖癌症、甲状腺问题、并发症、用药/治疗等常见临床问题模式
- Observations:
  - 在 LLM Planner 失败时，规则 fallback 不再明显主题漂移
- Insight:
  - Agent 系统中的 fallback 必须与问题主题保持一致，否则会让下游全部跑偏

## Experiment 5: First LLM Integration
- Goal:
  - 将系统从纯规则版推进到 LLM 驱动版
- Changes:
  - 新增统一 `llm.py`
  - 将 Planner、Extractor、Writer 改为优先调用 LLM，失败时 fallback 到规则版
- Observations:
  - 需要处理第三方兼容接口的 `base_url` 与返回格式适配问题
  - LLM Planner、Extractor、Writer 分别成功接入后，结果更自然、表达更接近真实助手
- Insight:
  - 统一 LLM 调用层 + 每节点 fallback 是构建稳健 agent 工作流的关键

## Experiment 6: Archive v0.1 and v0.2
- Goal:
  - 对版本演进进行正式归档
- Changes:
  - 初始化 git 仓库、配置 `.gitignore`
  - 提交并推送：
    - `v0.1 baseline workflow`
    - `v0.2 llm-driven workflow`
- Observations:
  - Windows 下 git HTTPS/TLS 链路存在兼容性问题，需要切换到 `schannel`
- Insight:
  - 可归档、可回退、可展示的版本历史本身就是 AI 应用工程能力的一部分

## Experiment 7: First Real Source Retrieval via PubMed
- Goal:
  - 用真实来源替换 mock 数据
- Changes:
  - 接入 PubMed `esearch` 获取 PMID
  - 接入 PubMed `efetch` 获取标题、摘要和年份
  - 将真实文献映射到 `SourceDocument`
- Observations:
  - 系统已能从真实 PubMed 文献构建输入，而不再依赖 `mock_sources.json`
- Insight:
  - 一旦使用真实来源，问题就从“流程能否运行”转向“检索质量是否足够好”

## Experiment 8: PubMed Direct-Through Workflow
- Goal:
  - 从“本地来源库 + 规则重排”转为“实时检索 -> 抽取 -> 总结”的直通流程
- Changes:
  - `source_mode=pubmed` 时，工作流直接使用 PubMed 检索结果
  - Verifier 重构为更通用的轻量审核器
- Observations:
  - 系统已经可以完成真实来源驱动的端到端闭环
- Insight:
  - 对当前项目而言，实时检索 + 抽取 + 总结比早期自建本地库更适合作为中期版本主线

## Experiment 9: Query Relaxation for PubMed
- Goal:
  - 解决专业关键词过多导致 PubMed 零结果的问题
- Changes:
  - 为 PubMed 检索增加结构化查询与逐级放宽策略：
    - 核心词 AND
    - 支持词 OR
    - 再退化到 broad search
- Observations:
  - 甲状腺肿大并发症等问题在放宽检索后开始稳定返回结果
- Insight:
  - 检索质量不仅依赖关键词专业度，还依赖查询语法是否兼顾召回率

## Experiment 10: Lightweight RAG Introduction
- Goal:
  - 将系统从“直接全量摘要喂给 LLM”升级到更接近 RAG 的流程
- Changes:
  - 新增 `rag/chunker.py`
  - 新增 chunk 级相关性检索
  - 在 PubMed 结果进入下游前先做 chunk 检索和高相关上下文回流
- Observations:
  - 系统开始不再只依赖整篇摘要，而是围绕更相关的局部片段组织证据
- Insight:
  - 即便不引入重型向量库，chunking + retrieval 也能显著提升 RAG 工作流的结构完整性

## Experiment 11: Source Scoring and Quality Weighting
- Goal:
  - 提升真实来源质量控制能力
- Changes:
  - 为 PubMed 直通模式补充 `relevance_score`
  - 自动识别 guideline / review / trial / case report 等文献类型
  - 根据文献类型和年份调整 `quality_score`
- Observations:
  - 系统不再把所有 PubMed 文献视为同等质量
  - Verifier 的置信度和风险判断更有依据
- Insight:
  - 医学证据系统的可信度，不仅依赖“有没有文献”，还依赖“文献类型和时效性”

## Experiment 12: Hybrid Retrieval and Local RAG Store
- Goal:
  - 把轻量 RAG 再往完整 RAG 方向推进
- Changes:
  - 新增本地 embedding（轻量 deterministic embedding）
  - 新增 hybrid retrieval：sparse + dense
  - 新增本地 `rag_store.json` 持久化
- Observations:
  - 系统具备了 chunk 持久化和检索复用能力
  - 检索不再只依赖关键词匹配
- Insight:
  - 当前项目已从简单 retrieval workflow 演进为轻量 RAG 工作流，但仍未达到重型向量数据库平台级形态

## Experiment 13: GUI Productization
- Goal:
  - 提升项目展示性和可交互性
- Changes:
  - 新增桌面 GUI
  - 支持进度条、阶段展示、历史记录、复制结果、导出结果、打开来源链接
- Observations:
  - 项目从命令行原型升级为可演示工具
- Insight:
  - 对面试项目来说，GUI 不是核心算法能力，但能显著提升完成度和作品感

## Experiment 14: Stable End-to-End Test on Thyroid Goiter Complications
- Question:
  - 甲状腺肿大会有什么并发症
- Observations:
  - Planner 生成了与 `goiter`、`thyroid enlargement`、`complications` 等匹配的检索词
  - PubMed 返回真实相关来源
  - Extractor 能抽取并发症、压迫症状、风险和干预信息
  - Writer 能生成结构化中文总结
  - 因来源偏旧、证据层级有限，系统仍给出人工审核提示
- Insight:
  - 当前系统已能在真实来源基础上完成通用医学问题的端到端处理

## Experiment 15: Final Positioning
- Current Position:
  - 一个面向医学问题的证据驱动型 Agent + 轻量 RAG 原型
- Strengths:
  - 真实来源
  - 多阶段工作流
  - LLM 节点
  - 轻量 RAG
  - GUI
- Remaining Gaps:
  - 还不是重型向量数据库 RAG 平台
  - 还缺多源检索、专业 reranker、更强审核层
- Final Insight:
  - 当前版本已经足够作为“可面试讲解的优秀 AI 应用项目”使用
