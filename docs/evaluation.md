# 评测

## Benchmark

当前 benchmark：

- `100` 条问题
- 覆盖 `30+` 常见病症主题

主要字段：

- `question_id`
- `question`
- `question_type`
- `risk_level`
- `gold_keywords`
- `mesh_terms`
- `gold_sources`
- `gold_claim`
- `needs_human_review`

## 方法对比

当前支持的方法：

- `direct_llm`
- `retrieve_then_summarize`
- `current_workflow`
- `workflow_with_rag_and_verifier`

## 消融实验

当前支持：

- `ablation_no_planner`
- `ablation_no_verifier`
- `ablation_no_rag`
- `ablation_rule_extractor_only`
- `ablation_no_source_type_weighting`

## 自动指标

- `retrieval_recall_at_k`
- `citation_precision`
- `claim_consistency`
- `hallucination_rate`
- `human_review_trigger_rate`

## 输出文件

完整评测默认输出到：

- `outputs/eval/`

快速评测默认输出到：

- `outputs/eval_quick/`

常见结果文件：

- `experiment_results.json`
- `ablation_results.json`
- `method_summary.csv`
- `ablation_summary.csv`
- `method_summary.md`
- `ablation_summary.md`
- `failure_cases.json`
- `success_cases.json`

## 异地反馈

如果需要远程人工反馈：

1. 先运行评测
2. 导出评审表 CSV
3. 上传到在线表格
4. 由异地填写

常用命令：

```bash
python -m medevidence_agent.main evaluate_quick
python -m medevidence_agent.main export_review_sheet
```

## 继续阅读

- 项目总览见：[overview.md](overview.md)
- 架构说明见：[architecture.md](architecture.md)
- 对外展示材料见：[presentation.md](presentation.md)
