import os
from dataclasses import dataclass
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv() -> None:
        return None


load_dotenv()


@dataclass
class Settings:
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_base_url: str = os.getenv("OPENAI_BASE_URL", "")
    openai_model: str = os.getenv("OPENAI_MODEL", "")
    source_mode: str = os.getenv("MEDEVIDENCE_SOURCE_MODE", "mock")

    use_mock: bool = os.getenv("MEDEVIDENCE_USE_MOCK", "true").lower() == "true"
    top_k: int = int(os.getenv("MEDEVIDENCE_TOP_K", "4"))
    evidence_score_threshold: float = float(
        os.getenv("MEDEVIDENCE_EVIDENCE_SCORE_THRESHOLD", "0.55")
    )
    confidence_threshold: float = float(
        os.getenv("MEDEVIDENCE_CONFIDENCE_THRESHOLD", "0.75")
    )
    rag_top_k_chunks: int = int(os.getenv("MEDEVIDENCE_RAG_TOP_K_CHUNKS", "6"))
    rag_dense_weight: float = float(os.getenv("MEDEVIDENCE_RAG_DENSE_WEIGHT", "0.5"))
    rag_sparse_weight: float = float(os.getenv("MEDEVIDENCE_RAG_SPARSE_WEIGHT", "0.5"))
    data_path: Path = Path(__file__).resolve().parents[2] / "data" / "mock_sources.json"
    rag_store_path: Path = Path(__file__).resolve().parents[2] / "data" / "rag_store.json"
    mesh_terms_path: Path = Path(__file__).resolve().parents[2] / "data" / "mesh_terms.json"


settings = Settings()
