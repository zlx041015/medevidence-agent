# Project Structure

## Root Directory

### `README.md`
项目总说明，介绍项目定位、目录结构、运行方式和学习顺序。

### `.env.example`
环境变量模板，展示项目需要哪些可配置项。

### `.env`
本地实际使用的环境变量配置文件。

### `pyproject.toml`
Python 项目的依赖和安装配置文件。

### `experiment_log.md`
记录项目迭代过程中的实验、参数调整、现象观察和结论。

---

## `data/`

### `mock_sources.json`
模拟医学资料库。  
用于在不接入真实搜索和数据库的情况下，先跑通整个工作流，并支持调参与模块验证。

---

## `docs/`

### `01_project_positioning.md`
项目定位，解释为什么做这个项目、解决什么问题、适合什么岗位。

### `02_build_flow.md`
项目制作流程，说明应该按什么顺序从 0 到 1 搭建系统。

### `03_architecture_and_tuning.md`
架构与调参说明，解释为什么采用工作流设计，以及主要参数的作用。

### `04_resume_and_interview.md`
简历与面试表达，帮助将项目转化成求职材料。

### `05_project_structure.md`
项目结构说明，用于梳理目录分层和模块职责。

---

## `src/medevidence_agent/`

这是项目核心代码目录。

### `main.py`
命令行入口。  
接收用户输入的问题，并调用主工作流运行整个系统。

### `config.py`
配置模块。  
负责读取 `.env` 中的参数，并统一提供给其他模块使用。

### `models.py`
数据模型模块。  
定义项目中核心的数据结构，例如问题、检索计划、来源文档、证据项、核验结果和最终答案。

### `workflow.py`
主工作流模块。  
负责按顺序调度 Planner、Retriever、Extractor、Verifier、Writer，并记录中间状态。

---

## `src/medevidence_agent/nodes/`

这里存放工作流中的核心处理节点。

### `planner.py`
负责将用户问题转成结构化检索计划，包括 intent、keywords 和风险等级。

### `extractor.py`
负责将候选来源转成结构化证据，并根据来源内容生成 claim。

### `verifier.py`
负责根据证据的分数、来源类型和 claim 内容，计算置信度、检测冲突，并生成总结性结论。

### `writer.py`
负责将核验结果整理成最终用户可读的答案，包括中文结论、置信度和引用列表。

---

## `src/medevidence_agent/tools/`

这里存放辅助工具模块。

### `storage.py`
负责读取本地 mock 数据文件，并转换为 `SourceDocument` 对象列表。

### `search.py`
负责对候选来源进行打分、过滤和排序，筛出更相关的资料进入后续流程。

---

## Current Workflow

当前最小工作流为：

`Clinical Question -> Planner -> Retriever -> Extractor -> Verifier -> Writer -> Final Answer`

---

## Design Principle

当前项目采用“工作流主导”的结构，而不是单轮大模型直接回答。  
这样设计的好处包括：

- 每个模块职责清晰
- 便于调试和定位问题
- 能保留中间结果和证据链
- 更适合后续扩展到 LangGraph、人工审核和前端系统

---

## Planned v0.3 Extension

### Goal
将当前基于本地 mock 数据的工作流，扩展为基于真实医学来源的 agent 工作流。

### Planned Source Flow
`Planner -> PubMed Search -> PubMed Fetch -> SourceDocument -> Retriever -> Extractor -> Verifier -> Writer`

### New Module to Add
- `src/medevidence_agent/tools/pubmed.py`

### Responsibility of `pubmed.py`
- 根据 Planner 生成的关键词搜索 PubMed
- 获取 PMID、标题、摘要、年份等文献信息
- 将结果转换为 `SourceDocument` 列表，供现有工作流继续使用

### Design Principle
v0.3 的核心不是推翻当前工作流，而是替换“来源获取方式”：
- v0.2：来源来自本地 mock 数据
- v0.3：来源来自真实 PubMed 检索结果