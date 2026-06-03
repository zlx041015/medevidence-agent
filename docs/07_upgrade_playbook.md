# 项目升级说明

## 本轮升级的重点

这轮升级的核心目标，是把项目从“少数专项病种示例”升级成“面向通用常见病症问题的医学证据系统原型”。

升级主要落在四个层面：

1. benchmark 从单一病种方向扩展为 30 多种常见病症
2. mock 与 guideline 来源从少量主题扩展为多病种来源集合
3. planner 与 verifier 的规则逻辑从专项识别扩展为通用病症识别
4. 项目文档和对外定位从专项 demo 统一切换到通用病症系统

## 当前 benchmark 特点

当前 benchmark：

- 题量：`100`
- 病种覆盖：`30+`
- 题型覆盖：
  - `treatment`
  - `screening`
  - `follow_up`
  - `risk_management`

## 当前来源数据特点

项目当前已经具备多病种 mock/guideline 数据，覆盖：

- 代谢性疾病
- 心血管疾病
- 呼吸系统疾病
- 感染性疾病
- 消化系统疾病
- 风湿免疫类疾病
- 泌尿系统疾病
- 精神心理问题
- 常见皮肤病

## 当前实验产物

运行：

```bash
python -m medevidence_agent.main evaluate
```

会生成：

- `outputs/eval/experiment_results.json`
- `outputs/eval/ablation_results.json`
- `outputs/eval/method_summary.csv`
- `outputs/eval/ablation_summary.csv`
- `outputs/eval/method_summary.md`
- `outputs/eval/ablation_summary.md`
- `outputs/eval/success_cases.json`
- `outputs/eval/failure_cases.json`

## 当前仍然是原型，不是最终临床平台

虽然项目已经具备多病种能力，但当前版本仍然更适合定义为：

`面向通用常见病症问题的可评测医学证据系统原型`

它还不是：

- 大规模真实临床知识平台
- 正式临床研究级 benchmark
- 全病种深度专家系统

## 后续最值得继续做的方向

1. 继续扩真实来源而不是只依赖 mock/guideline 样本
2. 用人工盲评或 judge model 增强 benchmark 质量
3. 为不同病种增加更细颗粒度的 gold claim 和 evidence level
4. 把界面升级为 Web 展示版
