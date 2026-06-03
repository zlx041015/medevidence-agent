# 项目结构说明

## 根目录

### `README.md`
项目总说明，包含项目定位、运行方式、benchmark 设计和简历表达建议。

### `.env.example`
环境变量模板，用于配置 OpenAI 兼容接口、模型名称和来源模式。

### `pyproject.toml`
Python 项目的依赖与安装配置文件。

### `experiment_log.md`
项目实验过程与迭代记录文件。

## `data/`

### `mock_sources.json`
本地 mock 医学来源数据，用于离线工作流测试，当前已扩展为多病种来源集合。

### `guideline_sources.json`
指南 / 综述 / 知识库风格来源数据，用于模拟多病种、多来源检索。

### `benchmark_questions.json`
当前 benchmark 问题集，覆盖 30 多种常见病症主题，用于 baseline、消融实验和自动评测。

### `rag_store.json`
本地轻量 RAG 存储文件。

### `history.json`
GUI 中历史问题记录文件。

## `docs/`

### `01_project_positioning.md`
项目定位与适合的面试讲法。

### `02_build_flow.md`
从零搭建工作流的思路说明。

### `03_architecture_and_tuning.md`
架构选择原因与调参建议。

### `04_resume_and_interview.md`
简历和面试表达建议。

### `05_project_structure.md`
当前项目结构与各模块职责说明。

### `06_interview_script.md`
适合面试中直接讲述的项目介绍稿。

### `07_upgrade_playbook.md`
本轮升级内容、实验产物和后续扩展方向说明。

### `07_resume_final.md`
升级后的简历项目表达版本。

### `08_full_code_and_architecture_guide.md`
更系统的代码结构、架构和迭代过程说明。

### `09_benchmark_guide.md`
benchmark 的病种分布、题型设计和使用说明。

## `src/medevidence_agent/`

### `main.py`
命令行入口，支持：
- 运行单个问题工作流
- 运行 benchmark、baseline 与消融实验

### `config.py`
环境变量读取与全局配置管理。

### `models.py`
定义问题、来源、证据、核验结果、benchmark 记录和实验运行结果等数据结构。

### `workflow.py`
负责按顺序调度 `Planner`、`Retriever`、`Extractor`、`Verifier`、`Writer`，并支持通过选项控制消融实验。

### `retrieval.py`
统一管理检索逻辑，封装 `mock`、`hybrid_mock`、`pubmed` 等模式。

### `gui.py`
图形界面入口，支持查看工作流过程、复制/导出结果和运行评测。

## `src/medevidence_agent/nodes/`

### `planner.py`
将用户问题转成结构化检索计划，包括：
- `intent`
- `keywords`
- 风险等级  
当前已支持较多常见病症关键词规则识别。

### `extractor.py`
将候选来源抽取为结构化证据，并支持 LLM 模式和规则模式切换。

### `verifier.py`
根据证据质量、来源等级、主题覆盖、时间有效性和冲突情况生成置信度与审核结论。  
当前已支持多病种主题识别。

### `writer.py`
将 verifier 结果整理为最终展示给用户的回答。

## `src/medevidence_agent/tools/`

### `storage.py`
读取本地数据文件并转换为 `SourceDocument`。

### `search.py`
提供关键词匹配与来源排序逻辑。

### `pubmed.py`
提供 PubMed 查询与文献抓取适配器。

## `src/medevidence_agent/rag/`

用于轻量 RAG：

- `chunker.py`：切块
- `embedder.py`：简单嵌入与相似度
- `retriever.py`：chunk 检索
- `store.py`：本地存储

## `src/medevidence_agent/eval/`

这是项目从 demo 升级为可评测系统的关键模块：

### `dataset.py`
加载 benchmark 数据集。

### `methods.py`
定义 baseline 方法和统一运行接口。

### `metrics.py`
定义自动评测指标。

### `runner.py`
批量运行实验、导出总表、生成成功/失败案例，并打印进度。

## 当前工作流主链

`临床问题 -> Planner -> Retriever -> Extractor -> Verifier -> Writer -> 最终回答`

## 当前设计原则

- 先保证离线可跑通，再逐步接入真实 API
- 先建立可解释工作流，再逐步增强模型能力
- 先形成评测闭环，再做更复杂的前端和部署
- 先扩展通用常见病症覆盖，再按需要深入专项病种
