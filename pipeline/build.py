import datetime
import json
import pathlib

import requests

from pipeline import sources as sources_mod
from pipeline.parse import parse_feature_list, parse_certification
from pipeline.validate import validate_record

FEATURE_SECTIONS = ("whats_new", "behavior_changes", "deprecated", "desupported")

def http_fetch(url):
    resp = requests.get(url, timeout=30, headers={"User-Agent": "oracle-version-diff/0.1"})
    resp.raise_for_status()
    return resp.text

def build_record(version, source_entry, fetch=http_fetch, today=None):
    today = today or datetime.date.today().isoformat()
    urls = source_entry["urls"]
    sections = {
        "certification": parse_certification(fetch(urls["certification"]), urls["certification"]),
    }
    for section in FEATURE_SECTIONS:
        sections[section] = parse_feature_list(fetch(urls[section]), urls[section])
    record = {
        "product": sources_mod.PRODUCT_ID,
        "version": version,
        "release_label": source_entry["release_label"],
        "last_updated": today,
        "sections": sections,
    }
    validate_record(record)
    return record

def write_outputs(sources, version_order, fetch=http_fetch, data_dir=None, today=None):
    data_dir = pathlib.Path(data_dir)
    product_dir = data_dir / sources_mod.PRODUCT_ID
    product_dir.mkdir(parents=True, exist_ok=True)

    versions_index = []
    # newest first in the index; order int: higher = newer
    for order, version in enumerate(version_order):
        record = build_record(version, sources[version], fetch=fetch, today=today)
        (product_dir / f"{version}.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
        versions_index.append({
            "version": version,
            "label": version,
            "order": order,
            "file": f"{sources_mod.PRODUCT_ID}/{version}.json",
        })
    versions_index.sort(key=lambda v: v["order"], reverse=True)

    index = {"products": [{
        "id": sources_mod.PRODUCT_ID,
        "label": sources_mod.PRODUCT_LABEL,
        "versions": versions_index,
    }]}
    (data_dir / "index.json").write_text(json.dumps(index, indent=2), encoding="utf-8")

def main():
    repo_root = pathlib.Path(__file__).resolve().parents[1]
    write_outputs(
        sources_mod.SOURCES,
        sources_mod.VERSION_ORDER,
        data_dir=repo_root / "data",
    )

if __name__ == "__main__":
    main()
