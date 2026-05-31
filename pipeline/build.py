import datetime
import json
import pathlib
import re

import requests

from pipeline import sources as sources_mod
from pipeline.parse import parse_feature_list, parse_certification, parse_release_sections
from pipeline.validate import validate_record

FEATURE_SECTIONS = ("whats_new", "behavior_changes", "deprecated", "desupported")

# Release-notes section page -> schema section. The deprecated page covers both
# deprecated and desupported; we place its items under "deprecated" for v1.
_RN_SECTIONS = ("whats_new", "behavior_changes", "deprecated")
_RN_TITLE_MATCH = {
    "whats_new": "New Features",
    "behavior_changes": "Default Behavior Changes",
    "deprecated": "Deprecated and Desupported",
}
_ALLOWED_INDEX_METADATA_KEYS = {"label", "support_track"}


def resolve_section_urls(toc_text, base_url):
    """Resolve section page URLs from a GoldenGate release-notes toc.js."""
    m = re.search(r"define\((.*)\);", toc_text, re.S)
    data = json.loads(m.group(1) if m else toc_text)
    topics = []
    for group in data.get("toc", []):
        topics.extend(group.get("topics", []))

    def find(title_substr):
        for t in topics:
            title = re.sub(r"<[^>]+>", "", t.get("title", "")).strip()
            if title_substr.lower() in title.lower():
                return base_url + t["href"]
        return None

    return {section: find(match) for section, match in _RN_TITLE_MATCH.items()}


def build_records(fetch, base_url, today=None):
    """Crawl the rolling release-notes stream into per-release version records."""
    today = today or datetime.date.today().isoformat()
    urls = resolve_section_urls(fetch(base_url + "toc.js"), base_url)
    section_releases = {
        section: parse_release_sections(fetch(url), url)
        for section, url in urls.items() if url
    }

    order_seq = []
    labels = {}
    released = {}
    for section in _RN_SECTIONS:
        for rel in section_releases.get(section, []):
            if rel["version"] not in labels:
                order_seq.append(rel["version"])
                labels[rel["version"]] = rel["label"]
                released[rel["version"]] = rel["released"]
            elif not released.get(rel["version"]) and rel["released"]:
                released[rel["version"]] = rel["released"]

    records = []
    for version in order_seq:
        sections = {s: [] for s in ("certification", *FEATURE_SECTIONS)}
        for section in _RN_SECTIONS:
            for rel in section_releases.get(section, []):
                if rel["version"] == version:
                    sections[section].extend(rel["items"])
        record = {
            "product": sources_mod.PRODUCT_ID,
            "version": version,
            "release_label": labels[version],
            "record_type": "release",
            "released": released[version],
            "last_updated": today,
            "sections": sections,
        }
        validate_record(record)
        records.append(record)
    release_records = sorted(records, key=lambda r: r["released"], reverse=True)
    baselines = []
    for baseline in sources_mod.STATIC_LEGACY_BASELINES:
        record = {**baseline, "last_updated": today}
        validate_record(record)
        baselines.append(record)
    for source in sources_mod.LEGACY_RELEASE_NOTE_SOURCES:
        record = build_legacy_release_note_record(source, fetch=fetch, today=today)
        validate_record(record)
        baselines.append(record)
    return release_records + sorted(baselines, key=lambda r: r["released"], reverse=True)


def build_legacy_release_note_record(source, fetch=None, today=None):
    """Build one legacy baseline from release-note section pages."""
    today = today or datetime.date.today().isoformat()
    fetch = fetch or http_fetch
    urls = source["urls"]
    sections = {s: [] for s in ("certification", *FEATURE_SECTIONS)}
    for section in _RN_SECTIONS:
        section_urls = urls[section]
        if isinstance(section_urls, str):
            section_urls = [section_urls]
        for url in section_urls:
            releases = parse_release_sections(fetch(url), url)
            for release in releases:
                sections[section].extend(release["items"])
    return {
        "product": source["product"],
        "version": source["version"],
        "release_label": source["release_label"],
        "record_type": source["record_type"],
        "released": source["released"],
        "last_updated": today,
        "sections": sections,
    }


def write_release_outputs(records, data_dir):
    """Write one JSON per release plus index.json (newest first, higher order = newer)."""
    data_dir = pathlib.Path(data_dir)
    product_dir = data_dir / sources_mod.PRODUCT_ID
    product_dir.mkdir(parents=True, exist_ok=True)

    n = len(records)
    versions_index = []
    for pos, record in enumerate(records):
        fname = f"{record['version']}.json"
        (product_dir / fname).write_text(json.dumps(record, indent=2), encoding="utf-8")
        versions_index.append({
            "version": record["version"],
            "label": record["version"],
            "order": n - pos,
            "record_type": record["record_type"],
            "released": record["released"],
            "file": f"{sources_mod.PRODUCT_ID}/{fname}",
        })

    index = {"products": [{
        "id": sources_mod.PRODUCT_ID,
        "label": sources_mod.PRODUCT_LABEL,
        "versions": versions_index,
    }]}
    (data_dir / "index.json").write_text(json.dumps(index, indent=2), encoding="utf-8")


def _index_entry(product_id, order, record, metadata):
    for key in metadata:
        if key not in _ALLOWED_INDEX_METADATA_KEYS:
            raise AssertionError(
                f"unsupported index metadata key {key!r} for {product_id} {record['version']}"
            )
    entry = {
        "version": record["version"],
        "label": record["version"],
        "order": order,
        "record_type": record["record_type"],
        "released": record["released"],
        "file": f"{product_id}/{record['version']}.json",
    }
    entry.update(metadata)
    return entry


def write_all_product_outputs(products, data_dir):
    data_dir = pathlib.Path(data_dir)
    index_products = []
    for product in products:
        product_dir = data_dir / product.product_id
        product_dir.mkdir(parents=True, exist_ok=True)
        records = sorted(product.records, key=lambda r: r["released"], reverse=True)
        expected_files = {f"{record['version']}.json" for record in records}
        for existing_file in product_dir.glob("*.json"):
            if existing_file.name not in expected_files:
                existing_file.unlink()
        n = len(records)
        versions_index = []
        metadata_by_version = product.index_metadata or {}
        for pos, record in enumerate(records):
            fname = f"{record['version']}.json"
            (product_dir / fname).write_text(json.dumps(record, indent=2), encoding="utf-8")
            versions_index.append(
                _index_entry(product.product_id, n - pos, record, metadata_by_version.get(record["version"], {}))
            )
        index_products.append({
            "id": product.product_id,
            "label": product.label,
            "versions": versions_index,
        })
    (data_dir / "index.json").write_text(json.dumps({"products": index_products}, indent=2), encoding="utf-8")


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
        "record_type": source_entry.get("record_type", "release"),
        "released": source_entry.get("released", today),
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

def today_iso():
    return datetime.date.today().isoformat()


def build_goldengate_product(fetch=None, today=None):
    from pipeline.product_registry import ProductBuild

    if fetch is None:
        fetch = http_fetch
    if today is None:
        today = today_iso()
    records = build_records(fetch, sources_mod.RELEASE_NOTES_BASE, today=today)
    return ProductBuild(sources_mod.PRODUCT_ID, sources_mod.PRODUCT_LABEL, records, {})

def main():
    from pipeline.product_registry import build_all_products

    repo_root = pathlib.Path(__file__).resolve().parents[1]
    products = build_all_products(fetch=http_fetch, today=today_iso())
    write_all_product_outputs(products, repo_root / "data")

if __name__ == "__main__":
    main()
