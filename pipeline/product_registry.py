from dataclasses import dataclass
from typing import Callable

from pipeline.validate import validate_record


@dataclass(frozen=True)
class ProductAdapter:
    product_id: str
    label: str
    build: Callable


@dataclass(frozen=True)
class ProductBuild:
    product_id: str
    label: str
    records: list[dict]
    index_metadata: dict[str, dict] | None = None


def registered_adapters():
    from pipeline import build
    from pipeline import curated

    return [
        ProductAdapter("oracle-goldengate", "Oracle GoldenGate", build.build_goldengate_product),
        ProductAdapter("oracle-database", "Oracle Database", curated.build_oracle_database_product),
        ProductAdapter("oracle-weblogic-server", "Oracle WebLogic Server", curated.build_oracle_weblogic_product),
    ]


def registered_product_ids(adapters=None):
    if adapters is None:
        adapters = registered_adapters()
    return {adapter.product_id for adapter in adapters}


def ensure_data_products_registered(index, registered_ids=None):
    if registered_ids is None:
        registered_ids = registered_product_ids()
    registered_ids = set(registered_ids)
    data_ids = {product["id"] for product in index.get("products", [])}
    missing = sorted(data_ids - registered_ids)
    if missing:
        raise AssertionError(f"Products missing refresh adapters: {', '.join(missing)}")


def build_all_products(adapters=None, fetch=None, today=None):
    if adapters is None:
        adapters = registered_adapters()
    products = []
    for adapter in adapters:
        result = adapter.build(fetch=fetch, today=today)
        if isinstance(result, ProductBuild):
            product_build = result
        else:
            product_build = ProductBuild(adapter.product_id, adapter.label, result, {})
        if product_build.product_id != adapter.product_id:
            raise AssertionError(
                f"{adapter.product_id} adapter returned {product_build.product_id} product"
            )
        for record in product_build.records:
            if record["product"] != adapter.product_id:
                raise AssertionError(
                    f"{adapter.product_id} adapter returned {record['product']} record"
                )
            validate_record(record)
        products.append(product_build)
    return products
