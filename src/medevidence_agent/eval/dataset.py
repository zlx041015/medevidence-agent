import json
from pathlib import Path

from medevidence_agent.models import BenchmarkQuestion


def load_benchmark_questions(path: Path) -> list[BenchmarkQuestion]:
    raw = json.loads(path.read_text(encoding="utf-8-sig"))
    return [BenchmarkQuestion(**item) for item in raw]
