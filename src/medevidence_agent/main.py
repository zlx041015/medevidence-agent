import sys
from pathlib import Path
from typing import Optional

from medevidence_agent.config import settings
from medevidence_agent.eval.runner import run_experiments
from medevidence_agent.workflow import run_workflow


def run_single_question(question: str) -> None:
    run_workflow(question, settings, verbose=True)


def _print_eval_progress(stage: str, method_name: str, question_id: str, current: int, total: int) -> None:
    if stage in ("准备阶段", "写出结果文件", "评测完成"):
        print(f"[{current}/{total}] {stage}")
        return
    print(f"[{current}/{total}] {stage} -> 方法: {method_name} -> 问题: {question_id}")


def run_evaluation(output_dir: str = "outputs/eval") -> None:
    print("开始运行完整评测，请稍候...")
    paths = run_experiments(
        settings,
        output_dir=Path(output_dir),
        progress_callback=_print_eval_progress,
    )
    print("结果文件如下：")
    for name, path in paths.items():
        print(f"{name}：{path}")


def run_quick_evaluation(output_dir: str = "outputs/eval_quick") -> None:
    print("开始运行快速评测，只跑少量样例与核心方法...")
    paths = run_experiments(
        settings,
        output_dir=Path(output_dir),
        progress_callback=_print_eval_progress,
        benchmark_limit=5,
        method_filter={"direct_llm", "retrieve_then_summarize", "workflow_with_rag_and_verifier"},
        ablation_filter={"ablation_no_verifier", "ablation_no_rag"},
    )
    print("快速评测结果文件如下：")
    for name, path in paths.items():
        print(f"{name}：{path}")


def main(argv: Optional[list[str]] = None) -> int:
    argv = argv or sys.argv[1:]
    if not argv:
        print("用法：")
        print("  python -m medevidence_agent.main main <问题文本>")
        print("  python -m medevidence_agent.main evaluate [输出目录]")
        print("  python -m medevidence_agent.main evaluate_quick [输出目录]")
        return 1

    command = argv[0]
    if command == "main":
        if len(argv) < 2:
            print("请输入一个医学问题。")
            return 1
        run_single_question(" ".join(argv[1:]))
        return 0

    if command == "evaluate":
        output_dir = argv[1] if len(argv) > 1 else "outputs/eval"
        run_evaluation(output_dir)
        return 0

    if command == "evaluate_quick":
        output_dir = argv[1] if len(argv) > 1 else "outputs/eval_quick"
        run_quick_evaluation(output_dir)
        return 0

    print(f"未知命令：{command}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
