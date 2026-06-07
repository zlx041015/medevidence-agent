# MedEvidence Agent

`MedEvidence Agent` 是一个面向通用常见病症问题的证据驱动型多智能体医学信息系统原型。

系统不直接依赖单轮大模型自由回答，而是通过多阶段工作流完成：

1. 问题规划
2. 来源检索
3. 证据抽取
4. 风险核验
5. 最终总结

## 核心能力

- 面向通用常见病症问题的多智能体工作流
- 检索增强与轻量 RAG
- 结构化证据抽取
- verifier 风险核验
- benchmark、baseline 与 ablation 评测
- GUI 演示与结果导出

## 运行环境

- Python 3.11

安装依赖：

```bash
pip install -e .
```

## 常用命令

运行单个问题：

```bash
python -m medevidence_agent.main main "高血压一线管理或治疗的核心是什么？"
```

运行快速评测：

```bash
python -m medevidence_agent.main evaluate_quick
```

运行完整评测：

```bash
python -m medevidence_agent.main evaluate
```

启动图形界面：

```bash
python -m medevidence_agent.gui
```

## 文档索引

### 对外说明

- [overview.md](docs/overview.md)
- [architecture.md](docs/architecture.md)
- [evaluation.md](docs/evaluation.md)
- [presentation.md](docs/presentation.md)

## 项目定位

该项目更适合定义为：

`一个面向通用常见病症问题的证据驱动型多智能体医学 AI 工作流原型`
