import copy
import json
import pathlib
from urllib.parse import urlparse

from pipeline.product_registry import ProductBuild
from pipeline.validate import validate_record

CURATED_SOURCE_DIR = pathlib.Path(__file__).resolve().parent / "curated_sources"


def oracle_owned_host(url):
    host = urlparse(url).hostname or ""
    return host == "oracle.com" or host.endswith(".oracle.com")


def _record_source_urls(record):
    urls = set()
    for items in record["sections"].values():
        for item in items:
            source_url = item.get("source_url")
            if source_url:
                urls.add(source_url)
    return sorted(urls)


def _verify_source_urls(record, fetch):
    for source_url in _record_source_urls(record):
        if not oracle_owned_host(source_url):
            raise AssertionError(
                f"non-Oracle source URL in {record['product']} {record['version']}: {source_url}"
            )
        fetch(source_url)


def load_source_definition(filename):
    path = CURATED_SOURCE_DIR / filename
    return json.loads(path.read_text(encoding="utf-8"))


def build_curated_product(source_definition, fetch, today):
    if fetch is None:
        from pipeline.build import http_fetch

        fetch = http_fetch
    records = []
    index_metadata = {}
    product = source_definition["product"]
    for version_entry in source_definition["versions"]:
        record = copy.deepcopy(version_entry["record"])
        record["last_updated"] = today
        _verify_source_urls(record, fetch)
        validate_record(record)
        records.append(record)
        index_metadata[record["version"]] = dict(version_entry.get("index", {}))
    return ProductBuild(product["id"], product["label"], records, index_metadata)


def build_oracle_database_product(fetch=None, today=None):
    from pipeline.build import today_iso

    if today is None:
        today = today_iso()
    return build_curated_product(
        load_source_definition("oracle-database.json"),
        fetch=fetch,
        today=today,
    )


def build_oracle_weblogic_product(fetch=None, today=None):
    from pipeline.build import today_iso

    if today is None:
        today = today_iso()
    return build_curated_product(
        load_source_definition("oracle-weblogic-server.json"),
        fetch=fetch,
        today=today,
    )
