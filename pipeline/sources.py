# Ordered oldest -> newest. `order` for index.json is derived from this list position.
PRODUCT_ID = "oracle-goldengate"
PRODUCT_LABEL = "Oracle GoldenGate"
DOCS_INDEX_URL = "https://docs.oracle.com/en/middleware/goldengate/index.html"

# version -> { release_label, urls: { section: url } }
SOURCES = {
    "21c": {
        "release_label": "Oracle GoldenGate 21c",
        "urls": {
            "certification": "https://docs.oracle.com/en/middleware/goldengate/core/21.3/certification.html",
            "whats_new": "https://docs.oracle.com/en/middleware/goldengate/core/21.3/whats-new.html",
            "behavior_changes": "https://docs.oracle.com/en/middleware/goldengate/core/21.3/whats-new.html",
            "deprecated": "https://docs.oracle.com/en/middleware/goldengate/core/21.3/whats-new.html",
            "desupported": "https://docs.oracle.com/en/middleware/goldengate/core/21.3/whats-new.html",
        },
    },
    "23ai": {
        "release_label": "Oracle GoldenGate 23ai",
        "urls": {
            "certification": "https://docs.oracle.com/en/middleware/goldengate/core/23/certification.html",
            "whats_new": "https://docs.oracle.com/en/middleware/goldengate/core/23/whats-new.html",
            "behavior_changes": "https://docs.oracle.com/en/middleware/goldengate/core/23/whats-new.html",
            "deprecated": "https://docs.oracle.com/en/middleware/goldengate/core/23/whats-new.html",
            "desupported": "https://docs.oracle.com/en/middleware/goldengate/core/23/whats-new.html",
        },
    },
}

VERSION_ORDER = list(SOURCES.keys())  # position == display order (higher index = newer)
