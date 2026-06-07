# 架构

## 设计原则

- 先证据，后结论
- 先结构化，后生成
- 先可控，后自治
- 先可评测，后扩展

## 多智能体层

系统将流程拆成五个独立 agent：

- `PlannerAgent`
- `RetrieverAgent`
- `ExtractorAgent`
- `VerifierAgent`
- `WriterAgent`

由 `MultiAgentCoordinator` 统一调度。

协调器负责：

- 顺序执行
- 轨迹记录
- 最大步数限制
- 重复执行检测

## 主要代码结构

### `src/medevidence_agent/`

- `main.py`：命令行入口
- `workflow.py`：主工作流入口
- `agents.py`：多智能体层与协调器
- `retrieval.py`：统一检索逻辑
- `llm.py`：模型调用封装
- `models.py`：核心数据结构
- `gui.py`：图形界面

### `src/medevidence_agent/nodes/`

- `planner.py`
- `extractor.py`
- `verifier.py`
- `writer.py`

### `src/medevidence_agent/rag/`

- `chunker.py`
- `embedder.py`
- `retriever.py`
- `store.py`

### `src/medevidence_agent/eval/`

- `dataset.py`
- `methods.py`
- `metrics.py`
- `runner.py`

## 当前关键取舍

### 为什么不用单个大 Prompt

因为医疗场景更强调：

- 可解释
- 可追溯
- 可调试
- 可核验

### 为什么先做轻量 RAG

因为当前阶段优先级是：

- 离线可跑
- 架构完整
- 便于展示和评测

### 为什么 verifier 独立存在

因为系统不仅要能回答，还要能判断：

- 主题是否匹配
- 证据是否足够
- 来源是否可靠
- 是否需要人工审核

## 当前调优重点

- 病种词与任务词分离
- 主题漂移控制
- 来源质量加权
- 输出的结论/风险分层

## 继续阅读

- 项目总览见：[overview.md](overview.md)
- 评测与 benchmark 见：[evaluation.md](evaluation.md)
- 如果需要简短对外介绍，见：[presentation.md](presentation.md)
