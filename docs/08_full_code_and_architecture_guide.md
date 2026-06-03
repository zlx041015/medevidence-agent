# 项目全代码与架构详解

## 一、项目的核心定位

`MedEvidence Agent` 不是一个只围绕某个专项疾病的小型问答 demo，而是一个面向通用常见病症问题的证据驱动型医学信息系统原型。

它的目标是解决这样的问题：

1. 医疗场景下，大模型直接回答容易出现幻觉
2. 结果即使流畅，也不一定能追溯到来源
3. 常见病症问题往往涉及筛查、随访、治疗、风险分层等多种任务
4. 如果没有 benchmark、baseline 和消融实验，很难证明系统为什么更好

所以这个项目真正想做的，不是“让模型答题”，而是：

`把通用病症问题转化为一个可检索、可抽取、可核验、可评测、可展示的证据工作流。`

## 二、为什么采用工作流主导架构

项目采用：

- `Planner`
- `Retriever`
- `Extractor`
- `Verifier`
- `Writer`

五阶段结构，而不是一个大 Prompt。

这样做的原因是：

- 每个节点职责清楚
- 便于调试和替换
- 便于加入 fallback
- 便于做 benchmark、baseline 和消融实验
- 便于记录中间状态和失败原因

## 三、为什么现在要做成通用病症系统

如果项目只围绕一两个病种示例，那么它更像一个演示脚本；  
而当它能覆盖高血压、糖尿病、慢阻肺、哮喘、冠心病、消化系统疾病、精神心理问题等常见场景时，它更像一个真正的医学信息系统原型。

这样做的价值是：

- 更适合面试讲述
- 更能体现系统设计能力
- 更像通用平台而不是专项样例

## 四、每个代码文件的作用

### `src/medevidence_agent/config.py`

负责读取环境变量和项目配置，包括：

- 模型配置
- 来源模式
- 阈值
- RAG 参数

### `src/medevidence_agent/models.py`

定义系统的数据结构，包括：

- 问题对象
- 检索计划
- 来源对象
- 证据对象
- verifier 结果
- 最终答案
- benchmark 记录
- 方法运行结果

### `src/medevidence_agent/llm.py`

统一封装模型调用。

### `src/medevidence_agent/workflow.py`

系统主调度器。负责串联：

- Planner
- Retriever
- Extractor
- Verifier
- Writer

同时支持通过 `WorkflowOptions` 做消融实验。

### `src/medevidence_agent/retrieval.py`

统一管理检索逻辑，包括：

- `mock`
- `hybrid_mock`
- `pubmed`

以及来源重排、RAG chunk 压缩等过程。

### `src/medevidence_agent/main.py`

命令行入口，支持：

- 单题运行
- 评测运行

### `src/medevidence_agent/gui.py`

图形界面入口，支持：

- 工作流展示
- 来源查看
- 结果复制/导出
- 评测结果预览

## `src/medevidence_agent/nodes/`

### `planner.py`

负责把问题转成检索计划。

当前已经从糖尿病/甲状腺专项规则扩展成多病种规则识别。

### `extractor.py`

负责从来源中抽取结构化证据。

### `verifier.py`

负责：

- 主题一致性
- 支撑强度
- 来源等级
- 时间有效性
- 冲突检测
- 人工审核触发

当前也已扩展为多病种主题识别。

### `writer.py`

负责整理最终输出。

## `src/medevidence_agent/tools/`

### `storage.py`

加载本地 JSON 来源。

### `search.py`

负责关键词重叠和基础重排。

### `pubmed.py`

负责 PubMed 查询和文献抓取。

## `src/medevidence_agent/rag/`

这一层构成轻量 RAG 能力：

- `chunker.py`
- `embedder.py`
- `retriever.py`
- `store.py`

## `src/medevidence_agent/eval/`

这是项目“从 demo 升级为可评测系统”的关键模块。

### `dataset.py`

读取 benchmark。

### `methods.py`

统一定义 baseline 和工作流方法。

### `metrics.py`

定义自动评测指标。

### `runner.py`

负责批量跑实验、写结果文件、生成成功/失败案例并打印进度。

## 五、数据与来源文件的作用

### `data/benchmark_questions.json`

当前 benchmark 数据集。

### `data/guideline_sources.json`

多病种 guideline / review 风格来源数据。

### `data/mock_sources.json`

通用 mock 来源数据，用于离线路径。

### `data/rag_store.json`

本地轻量 RAG 存储。

## 六、项目迭代过程

这个项目大致经历了几个阶段：

### 阶段 1：规则版工作流

目标是先让系统跑通。

### 阶段 2：接入 LLM

目标是让 Planner、Extractor、Writer 更自然。

### 阶段 3：接入真实来源与轻量 RAG

目标是从 mock 向真实证据链路过渡。

### 阶段 4：增强 verifier

目标是让系统在医疗场景下更可解释、更可控。

### 阶段 5：加入 benchmark、baseline、消融和 GUI

目标是把项目从 demo 升级成可评测作品。

### 阶段 6：从专项示例升级为通用病症系统

目标是：

- 从少病种示例扩展为多病种问题集
- 扩展多病种来源数据
- 扩展 planner/verifier 规则
- 统一文档叙事

## 七、为什么这样设计是合理的

### 1. 先结构化，再智能化

先搭建工作流结构，再逐步引入模型，比一开始全黑箱更稳定。

### 2. 先离线可跑，再接在线能力

离线能力保证开发可控，也方便展示。

### 3. 先有 benchmark，再谈“更强”

如果没有 benchmark、baseline 和消融实验，就很难真正说明系统提升。

### 4. 先做广谱原型，再做专病深化

当前你要的是一个适合简历和面试的通用系统原型，而不是某个单病种的研究平台。

## 八、一句话总结

`MedEvidence Agent` 的价值在于：它把“常见病症问题”转化成一个可检索、可抽取、可核验、可评测、可展示的医学证据系统，而不是一个只会直接生成答案的问答 demo。
