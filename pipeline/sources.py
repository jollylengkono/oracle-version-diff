# Ordered oldest -> newest. `order` for index.json is derived from this list position.
PRODUCT_ID = "oracle-goldengate"
PRODUCT_LABEL = "Oracle GoldenGate"
DOCS_INDEX_URL = "https://docs.oracle.com/en/middleware/goldengate/index.html"

# Rolling release-notes stream for the modern GoldenGate line (23.x / 26ai).
# build.build_records() reads `<base>toc.js` to resolve the section page URLs,
# so adding a future doc line only requires updating this base.
RELEASE_NOTES_BASE = "https://docs.oracle.com/en/database/goldengate/core/26/release-notes/"

STATIC_LEGACY_BASELINES = [
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
]

LEGACY_RELEASE_NOTE_SOURCES = [
    {
        "product": PRODUCT_ID,
        "version": "21c",
        "release_label": "Oracle GoldenGate 21c",
        "record_type": "baseline",
        "released": "2021-01-01",
        "urls": {
            "whats_new": [
                "https://docs.oracle.com/en/middleware/goldengate/core/21.3/release-notes/release-21.14.0.0.0-april-2024.html",
                "https://docs.oracle.com/en/middleware/goldengate/core/21.3/release-notes/release-21.12.0.0.4-november-2023-db2-i-update.html",
                "https://docs.oracle.com/en/middleware/goldengate/core/21.3/release-notes/release-21.10.0.0.0-april-2023-adb-update.html",
                "https://docs.oracle.com/en/middleware/goldengate/core/21.3/release-notes/release-21.4.0-october-2021.html",
                "https://docs.oracle.com/en/middleware/goldengate/core/21.3/release-notes/release-21.3.0-initial-release.html",
                "https://docs.oracle.com/en/middleware/goldengate/core/21.3/release-notes/oggcore-new-features-may-2021.html",
            ],
            "behavior_changes": "https://docs.oracle.com/en/middleware/goldengate/core/21.3/release-notes/default-behavior-changes.html",
            "deprecated": "https://docs.oracle.com/en/middleware/goldengate/core/21.3/release-notes/deprecated-features.html",
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
