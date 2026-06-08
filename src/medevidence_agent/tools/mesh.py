import json
from functools import lru_cache
from pathlib import Path


@lru_cache(maxsize=8)
def _load_mesh_terms_cached(path_str: str) -> dict:
    return json.loads(Path(path_str).read_text(encoding="utf-8-sig"))


def load_mesh_terms(path: Path) -> dict:
    return _load_mesh_terms_cached(str(path.resolve()))


def _entry_aliases(record: dict) -> list[str]:
    aliases = record.get("aliases", [])
    descriptor = record.get("descriptor_name", "")
    values = [descriptor] + aliases
    return [value for value in values if value]


def detect_mesh_terms(text: str, mesh_bundle: dict) -> list[str]:
    lowered = text.lower()
    matched: list[str] = []
    for ui, record in mesh_bundle.get("terms", {}).items():
        aliases = _entry_aliases(record)
        if any(alias in text or alias.lower() in lowered for alias in aliases):
            matched.append(record["descriptor_name"])
    return matched


def detect_mesh_records(text: str, mesh_bundle: dict) -> list[dict]:
    lowered = text.lower()
    matched: list[dict] = []
    for ui, record in mesh_bundle.get("terms", {}).items():
        aliases = _entry_aliases(record)
        if any(alias in text or alias.lower() in lowered for alias in aliases):
            matched.append(record)
    return matched


def mesh_terms_to_keywords(mesh_terms: list[str], mesh_bundle: dict) -> list[str]:
    keywords: list[str] = []
    term_records = mesh_bundle.get("terms", {})
    descriptor_lookup = {record["descriptor_name"]: record for record in term_records.values()}

    for mesh_term in mesh_terms:
        record = descriptor_lookup.get(mesh_term)
        if record is None:
            keywords.append(mesh_term.lower())
            continue
        keywords.append(record["descriptor_name"].lower())
        keywords.extend(alias.lower() for alias in record.get("aliases", [])[:3])

    return list(dict.fromkeys(keywords))
