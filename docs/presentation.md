# 展示

## 推荐项目定义

推荐定义为：

`一个面向通用常见病症问题的证据驱动型多智能体医学信息系统原型`

## 30 秒介绍

项目采用多智能体工作流结构，将医学问题拆成问题规划、来源检索、证据抽取、风险核验和最终总结五个阶段，目标是生成更可追溯、可解释的结果，而不是直接输出黑箱式答案。

## 2 分钟介绍

系统由 `PlannerAgent`、`RetrieverAgent`、`ExtractorAgent`、`VerifierAgent` 和 `WriterAgent` 组成，并由协调器统一编排。它支持 mock、hybrid_mock 和 PubMed 来源，内置 benchmark、baseline 和消融实验，可用于展示医疗 AI 工作流、RAG、风险核验和多智能体执行逻辑。

## 推荐亮点

- 多智能体工作流
- 证据驱动问答
- RAG 与来源追溯
- verifier 风险核验
- benchmark、baseline、ablation
- GUI 与结果导出

## 对外关键词

- multi-agent
- medical evidence
- RAG
- verifier
- benchmark
- ablation

## 继续阅读

- 项目总览见：[overview.md](overview.md)
- 架构说明见：[architecture.md](architecture.md)
- 评测说明见：[evaluation.md](evaluation.md)
