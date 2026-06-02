# Interview Script

## 30-Second Version

我做的是一个面向医学问题的证据驱动型 Agent 原型。它不是直接让大模型回答医学问题，而是先让系统基于真实 PubMed 文献做检索，再通过 LLM 进行问题规划、证据抽取和结果总结，同时用轻量审核机制控制风险。项目后期还加入了轻量 RAG、文献类型识别和 GUI 展示层。

## 2-Minute Version

这个项目的核心目标是解决医疗场景下“大模型直接回答不可靠”的问题。所以我把系统拆成几个清晰阶段：Planner、Retriever、Extractor、Verifier 和 Writer。

在版本演进上，v0.1 先是规则版 baseline workflow，用来验证整个工作流结构和参数调优；v0.2 把 Planner、Extractor、Writer 升级成了 LLM 驱动节点，形成了 llm-driven workflow；v0.3 则接入了 PubMed 真实来源，并加入轻量 RAG 能力，包括 chunking、chunk 级检索、hybrid retrieval 和本地 RAG store。

现在系统可以完成一个真实流程：用户输入一个医学问题，Planner 生成检索计划，系统去 PubMed 获取文献，抽取标题和摘要后切块检索，LLM Extractor 生成结构化证据，Verifier 做轻量审核和人工审核提示，最后由 LLM Writer 输出结构化中文总结。项目还带有一个桌面 GUI，支持进度条、历史记录、导出结果和打开来源链接。

## Architecture Highlights

### 1. Why not direct chat

我没有做医学聊天机器人，而是做证据驱动型工作流。这样可以减少幻觉，把来源、证据和结论尽量绑定起来。

### 2. Why multi-stage workflow

我把问题处理拆成多个节点，是为了让每一步职责清楚，也便于调试和后续升级。例如 Planner 负责检索词，Extractor 负责来源理解，Writer 负责表达，Verifier 负责风险提示。

### 3. Why lightweight RAG first

我没有一开始就上重型向量数据库，而是先做 lightweight RAG，把真实来源接进来，再补 chunking、hybrid retrieval 和本地 store。这是为了优先保证闭环成立，再逐步增强。

## Typical Follow-Up Questions

### Q1. 这算不算 RAG？

算是轻量 RAG。它已经有真实检索、chunking、chunk 级检索和基于检索结果回答的主链，但还不是完整向量数据库 RAG 平台，因为还没接专业 embedding 服务、重型向量索引和多源 reranker。

### Q2. 你这个项目最大的难点是什么？

最大的难点不是调用大模型 API，而是让系统在真实来源接入后仍然保持主题一致、检索可用和输出可信。实际问题包括第三方接口兼容、LLM fallback、PubMed 查询过严导致零结果、以及真实来源质量控制。

### Q3. 你是怎么控制幻觉的？

我用了几层策略：第一，系统不是直接回答，而是先检索来源；第二，Extractor 只做证据抽取；第三，Verifier 做轻量审核和人工审核提示；第四，Writer 只基于已核验内容组织输出。

### Q4. 如果继续做下去，你会补什么？

我会优先补三块：第一，多源检索，例如 Europe PMC 和指南官网；第二，更强的 RAG 层，例如外部 embedding 和向量索引；第三，更完整的证据审核，例如来源一致性和证据等级判断。

## Resume Bullet Draft

- 设计并实现面向医学问题的证据驱动型 Agent 工作流，将问题处理拆解为规划、真实来源检索、证据抽取、审核与总结五个阶段。
- 接入 PubMed 真实文献来源，构建 lightweight RAG 主链，支持 chunking、hybrid retrieval、本地 RAG store 与检索上下文回流。
- 基于兼容 OpenAI 接口实现 LLM Planner、Extractor 和 Writer，并通过 fallback 和轻量审核机制提升系统稳定性与可解释性。
- 开发桌面 GUI，支持进度展示、证据浏览、历史记录、结果导出与来源打开，提升项目可演示性与使用完整度。
