import json
from pathlib import Path

from medevidence_agent.models import SourceDocument


def load_mock_sources(path: Path) -> list[SourceDocument]:
    raw = json.loads(path.read_text(encoding="utf-8-sig"))
    return [SourceDocument(**item) for item in raw]
