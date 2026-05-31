import argparse
import copy
import datetime
import json
import pathlib

from pipeline.openai_extract import DEFAULT_MODEL, extract_candidates, require_openai_api_key
from pipeline.oracle_discovery import discover_oracle_pages, load_ai_source_targets, oracle_owned_url
from pipeline.validate import validate_record


class AIRefreshError(AssertionError):
    pass


REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
DEFAULT_SOURCE_PATHS = {
    "oracle-database": REPO_ROOT / "pipeline" / "curated_sources" / "oracle-database.json",
    "oracle-weblogic-server": REPO_ROOT / "pipeline" / "curated_sources" / "oracle-weblogic-server.json",
}


def today_iso():
    return datetime.date.today().isoformat()


def candidate_source_urls(record):
    urls = set()
    for items in record["sections"].values():
        for item in items:
            source_url = item.get("source_url")
            if source_url:
                urls.add(source_url)
    return sorted(urls)


def _validate_record_without_last_updated(record, today):
    validation_record = copy.deepcopy(record)
    validation_record["last_updated"] = today
    validate_record(validation_record)


def validate_candidate_payload(payload, product_id, today):
    if payload.get("product") != product_id:
        raise AIRefreshError(f"OpenAI candidate product mismatch: expected {product_id}, got {payload.get('product')}")
    for version_entry in payload.get("versions", []):
        index = version_entry.get("index", {})
        unsupported_index_keys = set(index) - {"label", "support_track"}
        if unsupported_index_keys:
            raise AIRefreshError(f"unsupported index metadata keys: {', '.join(sorted(unsupported_index_keys))}")
        record = version_entry["record"]
        if record.get("product") != product_id:
            raise AIRefreshError(f"candidate record product mismatch: {record.get('product')}")
        _validate_record_without_last_updated(record, today)
        for source_url in candidate_source_urls(record):
            if not oracle_owned_url(source_url):
                raise AIRefreshError(f"non-Oracle source_url rejected: {source_url}")
    return payload


def _entry_by_version(source_definition):
    return {
        entry["record"]["version"]: entry
        for entry in source_definition["versions"]
    }


def _clean_index(index):
    return {
        key: value
        for key, value in copy.deepcopy(index).items()
        if value is not None
    }


def merge_candidate_versions(source_definition, candidate_versions, today):
    merged = copy.deepcopy(source_definition)
    existing_by_version = _entry_by_version(merged)
    for candidate in candidate_versions:
        record = copy.deepcopy(candidate["record"])
        record.pop("last_updated", None)
        _validate_record_without_last_updated(record, today)
        version = record["version"]
        existing_index = existing_by_version.get(version, {}).get("index", {})
        candidate_index = _clean_index(candidate.get("index", {}))
        index = {**candidate_index, **existing_index}
        existing_by_version[version] = {"index": index, "record": record}
    merged["versions"] = sorted(
        existing_by_version.values(),
        key=lambda entry: entry["record"]["released"],
        reverse=True,
    )
    return merged


def _read_source(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _write_source(path, source_definition):
    path.write_text(f"{json.dumps(source_definition, indent=2)}\n", encoding="utf-8")


def _existing_versions(source_definition):
    return [entry["record"]["version"] for entry in source_definition["versions"]]


def run_ai_refresh(
    products,
    source_paths=None,
    targets=None,
    env=None,
    discover=None,
    extract=None,
    today=None,
    model=DEFAULT_MODEL,
):
    try:
        api_key = require_openai_api_key(env)
    except Exception as exc:
        raise AIRefreshError(str(exc)) from exc
    if today is None:
        today = today_iso()
    if source_paths is None:
        source_paths = DEFAULT_SOURCE_PATHS
    if targets is None:
        targets = load_ai_source_targets(REPO_ROOT / "pipeline" / "ai_sources.json")
    if discover is None:
        discover = discover_oracle_pages
    if extract is None:
        extract = extract_candidates
    for product_id in products:
        if product_id not in source_paths:
            raise AIRefreshError(f"unsupported AI refresh product: {product_id}")
        if product_id not in targets:
            raise AIRefreshError(f"missing AI source target for product: {product_id}")
        source_path = pathlib.Path(source_paths[product_id])
        source_definition = _read_source(source_path)
        target = targets[product_id]
        pages = discover(target["seed_urls"])
        payload = extract(
            api_key=api_key,
            product_id=product_id,
            product_label=target["label"],
            existing_versions=_existing_versions(source_definition),
            pages=pages,
            model=model,
        )
        payload = validate_candidate_payload(payload, product_id, today=today)
        updated = merge_candidate_versions(source_definition, payload["versions"], today=today)
        _write_source(source_path, updated)


def parse_args(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--products", nargs="+", default=["oracle-database", "oracle-weblogic-server"])
    parser.add_argument("--model", default=DEFAULT_MODEL)
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    run_ai_refresh(products=args.products, model=args.model)


if __name__ == "__main__":
    main()
