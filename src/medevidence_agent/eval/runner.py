import csv
import json
from dataclasses import asdict
from pathlib import Path
from typing import Callable, Optional, Set

from medevidence_agent.config import Settings
from medevidence_agent.eval.dataset import load_benchmark_questions
from medevidence_agent.eval.methods import MethodDefinition, build_method_definitions, run_method
from medevidence_agent.eval.metrics import score_result
from medevidence_agent.models import MethodRunResult, WorkflowOptions


ProgressCallback = Callable[[str, str, str, int, int], None]


ABLATION_DEFINITIONS = [
    MethodDefinition(
        name="ablation_no_planner",
        description="Workflow without planner stage.",
        options=WorkflowOptions(
            use_planner=False,
            use_verifier=True,
            use_rag=True,
            use_source_type_weighting=True,
            extractor_mode="auto",
            source_mode_override="hybrid_mock",
        ),
    ),
    MethodDefinition(
        name="ablation_no_verifier",
        description="Workflow without verifier stage.",
        options=WorkflowOptions(
            use_planner=True,
            use_verifier=False,
            use_rag=True,
            use_source_type_weighting=True,
            extractor_mode="auto",
            source_mode_override="hybrid_mock",
        ),
    ),
    MethodDefinition(
        name="ablation_no_rag",
        description="Workflow without chunk-level RAG retrieval.",
        options=WorkflowOptions(
            use_planner=True,
            use_verifier=True,
            use_rag=False,
            use_source_type_weighting=True,
            extractor_mode="auto",
            source_mode_override="hybrid_mock",
        ),
    ),
    MethodDefinition(
        name="ablation_rule_extractor_only",
        description="Workflow using rule-based extractor only.",
        options=WorkflowOptions(
            use_planner=True,
            use_verifier=True,
            use_rag=True,
            use_source_type_weighting=True,
            extractor_mode="rule",
            source_mode_override="hybrid_mock",
        ),
    ),
    MethodDefinition(
        name="ablation_no_source_type_weighting",
        description="Workflow without source type weighting.",
        options=WorkflowOptions(
            use_planner=True,
            use_verifier=True,
            use_rag=True,
            use_source_type_weighting=False,
            extractor_mode="auto",
            source_mode_override="hybrid_mock",
        ),
    ),
]


def _ensure_output_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _serialize_result(result: MethodRunResult, metrics: dict[str, float]) -> dict:
    payload = asdict(result)
    payload["metrics"] = metrics
    return payload


def _aggregate_rows(rows: list[dict]) -> list[dict]:
    grouped: dict[str, dict[str, float]] = {}
    counts: dict[str, int] = {}

    for row in rows:
        method_name = row["method_name"]
        grouped.setdefault(
            method_name,
            {
                "retrieval_recall_at_k": 0.0,
                "citation_precision": 0.0,
                "claim_consistency": 0.0,
                "hallucination_rate": 0.0,
                "human_review_trigger_rate": 0.0,
            },
        )
        counts[method_name] = counts.get(method_name, 0) + 1
        for key, value in row["metrics"].items():
            grouped[method_name][key] += value

    summary_rows = []
    for method_name, metrics in grouped.items():
        count = counts[method_name]
        summary = {"method_name": method_name}
        for key, value in metrics.items():
            summary[key] = round(value / count, 3)
        summary_rows.append(summary)
    return summary_rows


def _write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        return
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _write_markdown_summary(path: Path, title: str, rows: list[dict]) -> None:
    if not rows:
        path.write_text(f"# {title}\n\nNo rows generated.\n", encoding="utf-8")
        return
    headers = list(rows[0].keys())
    lines = [f"# {title}", "", "| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(row[column]) for column in headers) + " |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _build_failure_cases(result_rows: list[dict]) -> list[dict]:
    failures = []
    for row in result_rows:
        metrics = row["metrics"]
        if metrics["retrieval_recall_at_k"] < 0.5 or metrics["hallucination_rate"] > 0.5:
            failures.append(
                {
                    "method_name": row["method_name"],
                    "question_id": row["question_id"],
                    "question": row["question"],
                    "failure_reason": row["failure_reason"] or "; ".join(row["conflicts"]),
                    "summary_claim": row["summary_claim"],
                }
            )
    return failures


def _build_success_cases(result_rows: list[dict]) -> list[dict]:
    successes = []
    for row in result_rows:
        metrics = row["metrics"]
        if (
            metrics["retrieval_recall_at_k"] >= 0.5
            and metrics["citation_precision"] >= 0.5
            and metrics["hallucination_rate"] <= 0.5
        ):
            successes.append(
                {
                    "method_name": row["method_name"],
                    "question_id": row["question_id"],
                    "question": row["question"],
                    "summary_claim": row["summary_claim"],
                    "confidence": row["confidence"],
                }
            )
    return successes


def _emit_progress(
    callback: Optional[ProgressCallback],
    stage: str,
    method_name: str,
    question_id: str,
    current: int,
    total: int,
) -> None:
    if callback is not None:
        callback(stage, method_name, question_id, current, total)


def _run_batch(
    batch_name: str,
    definitions: list[MethodDefinition],
    benchmarks,
    settings: Settings,
    offset: int,
    total: int,
    progress_callback: Optional[ProgressCallback],
) -> tuple[list[dict], int]:
    rows: list[dict] = []
    current = offset
    for definition in definitions:
        for benchmark in benchmarks:
            current += 1
            _emit_progress(progress_callback, batch_name, definition.name, benchmark.question_id, current, total)
            result = run_method(definition, benchmark, settings)
            metrics = score_result(result, benchmark)
            rows.append(_serialize_result(result, metrics))
    return rows, current


def run_experiments(
    settings: Settings,
    output_dir: Path,
    progress_callback: Optional[ProgressCallback] = None,
    benchmark_limit: Optional[int] = None,
    method_filter: Optional[Set[str]] = None,
    ablation_filter: Optional[Set[str]] = None,
) -> dict[str, Path]:
    _ensure_output_dir(output_dir)
    benchmarks = load_benchmark_questions(settings.data_path.parent / "benchmark_questions.json")
    if benchmark_limit is not None:
        benchmarks = benchmarks[:benchmark_limit]

    method_definitions = build_method_definitions()
    ablation_definitions = ABLATION_DEFINITIONS

    if method_filter is not None:
        method_definitions = [definition for definition in method_definitions if definition.name in method_filter]
    if ablation_filter is not None:
        ablation_definitions = [definition for definition in ablation_definitions if definition.name in ablation_filter]

    total = len(method_definitions) * len(benchmarks) + len(ablation_definitions) * len(benchmarks)

    _emit_progress(progress_callback, "准备阶段", "-", "-", 0, total)

    result_rows, current = _run_batch(
        batch_name="baseline与主方法",
        definitions=method_definitions,
        benchmarks=benchmarks,
        settings=settings,
        offset=0,
        total=total,
        progress_callback=progress_callback,
    )

    ablation_rows, current = _run_batch(
        batch_name="消融实验",
        definitions=ablation_definitions,
        benchmarks=benchmarks,
        settings=settings,
        offset=current,
        total=total,
        progress_callback=progress_callback,
    )

    _emit_progress(progress_callback, "写出结果文件", "-", "-", current, total)

    result_json = output_dir / "experiment_results.json"
    result_json.write_text(json.dumps(result_rows, ensure_ascii=False, indent=2), encoding="utf-8")

    ablation_json = output_dir / "ablation_results.json"
    ablation_json.write_text(json.dumps(ablation_rows, ensure_ascii=False, indent=2), encoding="utf-8")

    summary_rows = _aggregate_rows(result_rows)
    ablation_summary_rows = _aggregate_rows(ablation_rows)
    _write_csv(output_dir / "method_summary.csv", summary_rows)
    _write_csv(output_dir / "ablation_summary.csv", ablation_summary_rows)
    _write_markdown_summary(output_dir / "method_summary.md", "Method Comparison", summary_rows)
    _write_markdown_summary(output_dir / "ablation_summary.md", "Ablation Comparison", ablation_summary_rows)

    failure_cases = _build_failure_cases(result_rows + ablation_rows)
    success_cases = _build_success_cases(result_rows + ablation_rows)
    (output_dir / "failure_cases.json").write_text(
        json.dumps(failure_cases, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (output_dir / "success_cases.json").write_text(
        json.dumps(success_cases, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    _emit_progress(progress_callback, "评测完成", "-", "-", total, total)

    return {
        "results": result_json,
        "ablations": ablation_json,
        "method_summary": output_dir / "method_summary.md",
        "ablation_summary": output_dir / "ablation_summary.md",
        "failure_cases": output_dir / "failure_cases.json",
        "success_cases": output_dir / "success_cases.json",
    }
