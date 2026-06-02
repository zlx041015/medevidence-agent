# MedEvidence Agent

面向临床问题的医学证据检索与结论生成系统实训项目。

这个项目不是单纯的聊天机器人，而是一个有明确工作流的 `evidence-driven agent`：

1. 接收一个临床问题
2. 拆解检索计划
3. 搜索候选证据
4. 抽取结构化信息
5. 交叉验证结论
6. 生成带引用的回答与后续建议

## 为什么这个项目适合你

- 贴合 `生物医学工程 / 医学信息工程` 背景
- 能体现 `AI 应用工程` 能力
- 能讲清楚 `医疗场景安全性`、`证据链`、`人工审核`
- 容易扩展为简历项目、比赛项目、科研工具

## 当前版本包含什么

- 可学习的项目结构
- 从 0 到 1 的制作流程文档
- 每个模块为什么这样设计的解释
- 可运行的最小代码骨架
- 参数调优与架构升级建议
- 本地 mock 数据，方便你先跑通流程

## 目录结构

```text
.
├─ docs/
│  ├─ 01_project_positioning.md
│  ├─ 02_build_flow.md
│  ├─ 03_architecture_and_tuning.md
│  └─ 04_resume_and_interview.md
├─ data/
│  └─ mock_sources.json
├─ src/
│  └─ medevidence_agent/
│     ├─ nodes/
│     ├─ tools/
│     ├─ __init__.py
│     ├─ config.py
│     ├─ main.py
│     ├─ models.py
│     └─ workflow.py
├─ .env.example
└─ pyproject.toml
```

## 先学什么

建议按这个顺序看：

1. [docs/01_project_positioning.md](E:/agent/docs/01_project_positioning.md)
2. [docs/02_build_flow.md](E:/agent/docs/02_build_flow.md)
3. [src/medevidence_agent/workflow.py](E:/agent/src/medevidence_agent/workflow.py)
4. [docs/03_architecture_and_tuning.md](E:/agent/docs/03_architecture_and_tuning.md)
5. [docs/04_resume_and_interview.md](E:/agent/docs/04_resume_and_interview.md)

## 环境准备

建议 Python `3.11+`。

安装依赖：

```bash
pip install -e .
```

复制环境变量模板：

```bash
copy .env.example .env
```

## 运行最小 Demo

```bash
python -m medevidence_agent.main "2型糖尿病合并高血压患者的一线治疗建议是什么？"
```

当前默认使用本地 mock 数据，不需要联网和 API Key。

## 你后面要做的升级

第一阶段：
- 看懂工作流
- 用 mock 数据跑通
- 学会调整 `top_k`、置信度阈值、节点职责

第二阶段：
- 接入真实搜索 API
- 接入 OpenAI / 其他 LLM
- 增加网页抓取与引用附录

第三阶段：
- 增加人工审批
- 增加评测集
- 增加前端页面或 FastAPI 接口

## 这个项目最重要的学习点

不是“怎么让模型回答医学问题”，而是：

- 怎么限制模型只基于证据说话
- 怎么把长任务拆成稳定的节点
- 怎么让结论可追溯
- 怎么设计调参和评测闭环
