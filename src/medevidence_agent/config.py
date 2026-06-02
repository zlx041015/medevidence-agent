import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()


@dataclass
class Settings:
    use_mock: bool = os.getenv("MEDEVIDENCE_USE_MOCK", "true").lower() == "true"
    top_k: int = int(os.getenv("MEDEVIDENCE_TOP_K", "3"))
    evidence_score_threshold: float = float(
        os.getenv("MEDEVIDENCE_EVIDENCE_SCORE_THRESHOLD", "0.55")
    )
    confidence_threshold: float = float(
        os.getenv("MEDEVIDENCE_CONFIDENCE_THRESHOLD", "0.70")
    )
    data_path: Path = Path(__file__).resolve().parents[2] / "data" / "mock_sources.json"


settings = Settings()