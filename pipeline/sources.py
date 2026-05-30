# Ordered oldest -> newest. `order` for index.json is derived from this list position.
PRODUCT_ID = "oracle-goldengate"
PRODUCT_LABEL = "Oracle GoldenGate"
DOCS_INDEX_URL = "https://docs.oracle.com/en/middleware/goldengate/index.html"

# Rolling release-notes stream for the modern GoldenGate line (23.x / 26ai).
# build.build_records() reads `<base>toc.js` to resolve the section page URLs,
# so adding a future doc line only requires updating this base.
RELEASE_NOTES_BASE = "https://docs.oracle.com/en/database/goldengate/core/26/release-notes/"

LEGACY_BASELINES = [
    {
        "product": PRODUCT_ID,
        "version": "19c",
        "release_label": "Oracle GoldenGate 19c",
        "record_type": "baseline",
        "released": "2019-01-01",
        "sections": {
            "certification": [],
            "whats_new": [],
            "behavior_changes": [],
            "deprecated": [],
            "desupported": [],
        },
    },
    {
        "product": PRODUCT_ID,
        "version": "21c",
        "release_label": "Oracle GoldenGate 21c",
        "record_type": "baseline",
        "released": "2021-01-01",
        "sections": {
            "certification": [],
            "whats_new": [],
            "behavior_changes": [],
            "deprecated": [],
            "desupported": [],
        },
    },
]

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
