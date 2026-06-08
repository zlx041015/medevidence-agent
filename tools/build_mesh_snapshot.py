import json
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.request import urlretrieve


MESH_XML_URL = "https://nlmpubs.nlm.nih.gov/projects/mesh/MESH_FILES/xmlmesh/desc2026.xml"


def download_mesh_xml(target_path: Path) -> Path:
    target_path.parent.mkdir(parents=True, exist_ok=True)
    urlretrieve(MESH_XML_URL, target_path)
    return target_path


def parse_mesh_xml(xml_path: Path) -> dict:
    root = ET.fromstring(xml_path.read_text(encoding="utf-8"))
    records: dict[str, dict] = {}

    for descriptor in root.findall(".//DescriptorRecord"):
        ui = descriptor.findtext("DescriptorUI", default="").strip()
        name = descriptor.findtext("DescriptorName/String", default="").strip()
        if not ui or not name:
            continue

        aliases: list[str] = []
        for term in descriptor.findall(".//TermList/Term/String"):
            value = (term.text or "").strip()
            if value and value != name and value not in aliases:
                aliases.append(value)

        tree_numbers: list[str] = []
        for tree in descriptor.findall(".//TreeNumberList/TreeNumber"):
            value = (tree.text or "").strip()
            if value:
                tree_numbers.append(value)

        records[ui] = {
            "mesh_ui": ui,
            "descriptor_name": name,
            "aliases": aliases,
            "tree_numbers": tree_numbers,
        }

    return {
        "source": "NLM MeSH XML 2026",
        "terms": records,
    }


def save_snapshot(snapshot: dict, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8-sig")
    return output_path


def main() -> None:
    root = Path("data")
    xml_path = root / "mesh_desc2026.xml"
    json_path = root / "mesh_terms.json"

    download_mesh_xml(xml_path)
    snapshot = parse_mesh_xml(xml_path)
    save_snapshot(snapshot, json_path)
    print(f"Saved MeSH snapshot to {json_path}")


if __name__ == "__main__":
    main()
