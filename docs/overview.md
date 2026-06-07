# 概览

## 项目定义

`MedEvidence Agent` 是一个面向通用常见病症问题的证据驱动型多智能体医学信息系统原型。

系统不直接让模型自由回答，而是先完成：

1. 问题规划
2. 来源检索
3. 证据抽取
4. 风险核验
5. 最终总结

## 核心能力

- 面向通用病症问题的医学问答工作流
- 多智能体执行结构
- 检索增强与轻量 RAG
- 证据抽取与风险核验
- benchmark、baseline、ablation 评测
- GUI 展示与结果导出

## 当前边界

当前版本适合：

- 原型展示
- benchmark 演示
- 医疗 AI 工作流讲解

当前版本不是：

- 正式临床决策系统
- 大规模真实医疗知识平台
- 专病深度专家系统

## 当前主流程

```text
Clinical Question
  -> PlannerAgent
  -> RetrieverAgent
  -> ExtractorAgent
  -> VerifierAgent
  -> WriterAgent
  -> Final Answer
```

## 继续阅读

- 架构说明见：[architecture.md](architecture.md)
- 评测说明见：[evaluation.md](evaluation.md)
- 对外展示材料见：[presentation.md](presentation.md)
