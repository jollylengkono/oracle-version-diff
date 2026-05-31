# AI-Assisted Data Refresh Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a manual GitHub Actions path that uses OpenAI from repository automation to propose Oracle-sourced Database and WebLogic curated data updates.

**Architecture:** Keep OpenAI behind a controlled Python pipeline. `oracle_discovery.py` owns Oracle-only URL filtering and page fetching, `openai_extract.py` owns the raw OpenAI Responses API request and structured response parsing, and `ai_refresh.py` owns candidate validation plus curated-source merging. The GitHub workflow calls the AI refresh first, then runs the deterministic `pipeline.build` and opens a review PR.

**Tech Stack:** Python 3.11, `requests`, `beautifulsoup4`, `jsonschema`, pytest, OpenAI Responses API over HTTPS, GitHub Actions.

---

## File Structure

- Create `pipeline/oracle_discovery.py`: Oracle-owned URL checks, page fetching with redirect validation, source-page discovery from checked-in product seed URLs.
- Create `pipeline/ai_sources.json`: product seed URLs for AI-assisted Database and WebLogic discovery.
- Create `pipeline/openai_extract.py`: OpenAI API key validation, structured-output schema, Responses API payload construction, response JSON extraction.
- Create `pipeline/ai_refresh.py`: CLI orchestration, candidate validation, curated-source merge, curated-source file writes.
- Create `.github/workflows/ai-refresh-data.yml`: manual-only AI-assisted workflow using `secrets.OPENAI_API_KEY`.
- Create tests under `tests/python/`: discovery guardrails, OpenAI payload/response handling, source merge behavior, workflow contract.

## Task 1: Oracle-Only Discovery Helpers

**Files:**
- Create: `tests/python/test_oracle_discovery.py`
- Create: `pipeline/oracle_discovery.py`
- Create: `pipeline/ai_sources.json`

- [ ] **Step 1: Write failing discovery tests**

Create `tests/python/test_oracle_discovery.py`:

```python
import pytest

from pipeline.oracle_discovery import (
    OracleSourceError,
    discover_oracle_pages,
    fetch_oracle_page,
    load_ai_source_targets,
    oracle_owned_url,
    require_oracle_url,
    unique_oracle_urls,
)


class FakeResponse:
    def __init__(self, text, url, status_error=None):
        self.text = text
        self.url = url
        self._status_error = status_error

    def raise_for_status(self):
        if self._status_error:
            raise self._status_error


class FakeSession:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def get(self, url, timeout, headers, allow_redirects):
        self.calls.append((url, timeout, headers["User-Agent"], allow_redirects))
        return self.responses.pop(0)


def test_oracle_owned_url_accepts_only_oracle_hosts():
    assert oracle_owned_url("https://oracle.com/a")
    assert oracle_owned_url("https://docs.oracle.com/a")
    assert oracle_owned_url("https://blogs.oracle.com/a")
    assert not oracle_owned_url("https://example.com/a")
    assert not oracle_owned_url("https://oracle.com.example.com/a")
    assert not oracle_owned_url("ftp://docs.oracle.com/a")


def test_require_oracle_url_rejects_non_oracle_url():
    with pytest.raises(OracleSourceError, match="non-Oracle"):
        require_oracle_url("https://example.com/a")


def test_fetch_oracle_page_rejects_non_oracle_redirect():
    session = FakeSession([FakeResponse("<html></html>", "https://example.com/final")])

    with pytest.raises(OracleSourceError, match="redirected"):
        fetch_oracle_page("https://docs.oracle.com/start", session=session)


def test_fetch_oracle_page_returns_final_oracle_page():
    session = FakeSession([FakeResponse("<html><title>Doc</title></html>", "https://docs.oracle.com/final")])

    page = fetch_oracle_page("https://docs.oracle.com/start", session=session)

    assert page.url == "https://docs.oracle.com/final"
    assert page.content == "<html><title>Doc</title></html>"
    assert session.calls == [("https://docs.oracle.com/start", 30, "oracle-version-diff/0.1", True)]


def test_unique_oracle_urls_normalizes_and_deduplicates():
    urls = unique_oracle_urls([
        "https://docs.oracle.com/a#section",
        "https://docs.oracle.com/a",
        "https://example.com/b",
        "/relative",
    ], base_url="https://docs.oracle.com/root/index.html")

    assert urls == [
        "https://docs.oracle.com/a",
        "https://docs.oracle.com/relative",
    ]


def test_discover_oracle_pages_fetches_seed_and_matching_links():
    seed_html = """
    <html><body>
      <a href="/en/database/oracle/oracle-database/26/nfcoa/all-nfg.html">26ai features</a>
      <a href="https://example.com/not-allowed.html">External</a>
      <a href="/en/database/oracle/oracle-database/26/upgrd/oracle-database-changes-deprecations-desupports.html">Upgrade</a>
    </body></html>
    """
    session = FakeSession([
        FakeResponse(seed_html, "https://docs.oracle.com/en/database/oracle/oracle-database/index.html"),
        FakeResponse("<html>features</html>", "https://docs.oracle.com/en/database/oracle/oracle-database/26/nfcoa/all-nfg.html"),
        FakeResponse("<html>upgrade</html>", "https://docs.oracle.com/en/database/oracle/oracle-database/26/upgrd/oracle-database-changes-deprecations-desupports.html"),
    ])

    pages = discover_oracle_pages(
        ["https://docs.oracle.com/en/database/oracle/oracle-database/index.html"],
        session=session,
        max_linked_pages=2,
    )

    assert [page.url for page in pages] == [
        "https://docs.oracle.com/en/database/oracle/oracle-database/index.html",
        "https://docs.oracle.com/en/database/oracle/oracle-database/26/nfcoa/all-nfg.html",
        "https://docs.oracle.com/en/database/oracle/oracle-database/26/upgrd/oracle-database-changes-deprecations-desupports.html",
    ]


def test_ai_source_targets_include_database_and_weblogic(repo_root):
    targets = load_ai_source_targets(repo_root / "pipeline" / "ai_sources.json")

    assert set(targets) == {"oracle-database", "oracle-weblogic-server"}
    assert targets["oracle-database"]["label"] == "Oracle Database"
    assert all(oracle_owned_url(url) for url in targets["oracle-database"]["seed_urls"])
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
.venv/bin/python -m pytest tests/python/test_oracle_discovery.py -q
```

Expected: FAIL with `ModuleNotFoundError: No module named 'pipeline.oracle_discovery'`.

- [ ] **Step 3: Add AI source seed configuration**

Create `pipeline/ai_sources.json`:

```json
{
  "oracle-database": {
    "label": "Oracle Database",
    "seed_urls": [
      "https://docs.oracle.com/en/database/oracle/oracle-database/index.html",
      "https://docs.oracle.com/en/database/oracle/oracle-database/26/index.html"
    ]
  },
  "oracle-weblogic-server": {
    "label": "Oracle WebLogic Server",
    "seed_urls": [
      "https://docs.oracle.com/en/middleware/standalone/weblogic-server/index.html",
      "https://docs.oracle.com/en/middleware/fusion-middleware/weblogic-server/index.html"
    ]
  }
}
```

- [ ] **Step 4: Implement discovery helpers**

Create `pipeline/oracle_discovery.py`:

```python
from dataclasses import dataclass
import json
from urllib.parse import urldefrag, urljoin, urlparse

from bs4 import BeautifulSoup
import requests

USER_AGENT = "oracle-version-diff/0.1"
LINK_HINTS = (
    "release",
    "notes",
    "whats-new",
    "newft",
    "nfcoa",
    "upgrd",
    "deprec",
    "desupport",
    "weblogic",
    "database",
)


class OracleSourceError(AssertionError):
    pass


@dataclass(frozen=True)
class OraclePage:
    url: str
    content: str


def oracle_owned_url(url):
    parsed = urlparse(url)
    host = parsed.hostname or ""
    return parsed.scheme in ("http", "https") and (host == "oracle.com" or host.endswith(".oracle.com"))


def require_oracle_url(url):
    if not oracle_owned_url(url):
        raise OracleSourceError(f"non-Oracle URL rejected: {url}")
    return url


def unique_oracle_urls(urls, base_url):
    seen = set()
    result = []
    for url in urls:
        absolute = urljoin(base_url, url)
        clean_url = urldefrag(absolute).url
        if clean_url in seen or not oracle_owned_url(clean_url):
            continue
        seen.add(clean_url)
        result.append(clean_url)
    return result


def fetch_oracle_page(url, session=None):
    require_oracle_url(url)
    session = session or requests.Session()
    response = session.get(
        url,
        timeout=30,
        headers={"User-Agent": USER_AGENT},
        allow_redirects=True,
    )
    response.raise_for_status()
    final_url = response.url or url
    if not oracle_owned_url(final_url):
        raise OracleSourceError(f"Oracle URL redirected to non-Oracle URL: {final_url}")
    return OraclePage(final_url, response.text)


def _candidate_links(page):
    soup = BeautifulSoup(page.content, "html.parser")
    hrefs = [a.get("href") for a in soup.find_all("a") if a.get("href")]
    urls = unique_oracle_urls(hrefs, page.url)
    return [
        url for url in urls
        if any(hint in url.lower() for hint in LINK_HINTS)
    ]


def discover_oracle_pages(seed_urls, session=None, max_linked_pages=12):
    pages = []
    linked_urls = []
    for seed_url in seed_urls:
        seed_page = fetch_oracle_page(seed_url, session=session)
        pages.append(seed_page)
        linked_urls.extend(_candidate_links(seed_page))
    for url in linked_urls[:max_linked_pages]:
        pages.append(fetch_oracle_page(url, session=session))
    return pages


def load_ai_source_targets(path):
    targets = json.loads(path.read_text(encoding="utf-8"))
    for product_id, target in targets.items():
        if not target.get("label"):
            raise OracleSourceError(f"AI source target missing label: {product_id}")
        for url in target.get("seed_urls", []):
            require_oracle_url(url)
    return targets
```

- [ ] **Step 5: Run tests and commit**

```bash
.venv/bin/python -m pytest tests/python/test_oracle_discovery.py -q
git add tests/python/test_oracle_discovery.py pipeline/oracle_discovery.py pipeline/ai_sources.json
git commit -m "feat: add Oracle-only AI discovery helpers"
```

Expected: tests pass.

## Task 2: OpenAI Structured Extraction Client

**Files:**
- Create: `tests/python/test_openai_extract.py`
- Create: `pipeline/openai_extract.py`

- [ ] **Step 1: Write failing OpenAI client tests**

Create `tests/python/test_openai_extract.py`:

```python
import json

import pytest

from pipeline.openai_extract import (
    OpenAIExtractionError,
    build_extraction_payload,
    extract_candidates,
    parse_response_json,
    require_openai_api_key,
)
from pipeline.oracle_discovery import OraclePage


class FakeResponse:
    def __init__(self, payload, status_error=None):
        self._payload = payload
        self._status_error = status_error

    def raise_for_status(self):
        if self._status_error:
            raise self._status_error

    def json(self):
        return self._payload


def _valid_candidate_payload():
    return {
        "product": "oracle-database",
        "versions": [
            {
                "index": {"label": "Oracle Database 27ai"},
                "record": {
                    "product": "oracle-database",
                    "version": "27ai",
                    "release_label": "Oracle Database 27ai",
                    "record_type": "release",
                    "released": "2027-01-01",
                    "sections": {
                        "certification": [],
                        "whats_new": [
                            {
                                "title": "Feature",
                                "description": "A sourced feature.",
                                "source_url": "https://docs.oracle.com/database/feature",
                            }
                        ],
                        "behavior_changes": [],
                        "deprecated": [],
                        "desupported": [],
                    },
                },
            }
        ],
    }


def test_require_openai_api_key_fails_when_missing():
    with pytest.raises(OpenAIExtractionError, match="OPENAI_API_KEY"):
        require_openai_api_key({})


def test_require_openai_api_key_returns_key():
    assert require_openai_api_key({"OPENAI_API_KEY": "sk-test"}) == "sk-test"


def test_build_extraction_payload_uses_structured_outputs_schema():
    pages = [OraclePage("https://docs.oracle.com/a", "<html>Oracle Database 27ai</html>")]

    payload = build_extraction_payload(
        product_id="oracle-database",
        product_label="Oracle Database",
        existing_versions=["26ai"],
        pages=pages,
        model="gpt-5",
    )

    assert payload["model"] == "gpt-5"
    assert payload["text"]["format"]["type"] == "json_schema"
    assert payload["text"]["format"]["strict"] is True
    assert payload["text"]["format"]["name"] == "oracle_release_delta_candidates"
    assert payload["text"]["format"]["schema"]["additionalProperties"] is False
    assert "Oracle-owned" in payload["instructions"]
    assert "https://docs.oracle.com/a" in payload["input"]


def test_parse_response_json_reads_output_text():
    payload = _valid_candidate_payload()
    response = {
        "output": [
            {
                "type": "message",
                "content": [
                    {"type": "output_text", "text": json.dumps(payload)}
                ],
            }
        ]
    }

    assert parse_response_json(response) == payload


def test_parse_response_json_rejects_refusal():
    response = {
        "output": [
            {
                "type": "message",
                "content": [
                    {"type": "refusal", "refusal": "No"}
                ],
            }
        ]
    }

    with pytest.raises(OpenAIExtractionError, match="refused"):
        parse_response_json(response)


def test_extract_candidates_posts_to_responses_api():
    calls = []

    def post(url, headers, json, timeout):
        calls.append((url, headers, json, timeout))
        return FakeResponse({
            "output": [
                {
                    "type": "message",
                    "content": [
                        {"type": "output_text", "text": '{"product":"oracle-database","versions":[]}'}
                    ],
                }
            ]
        })

    result = extract_candidates(
        api_key="sk-test",
        product_id="oracle-database",
        product_label="Oracle Database",
        existing_versions=["26ai"],
        pages=[OraclePage("https://docs.oracle.com/a", "<html></html>")],
        post=post,
        model="gpt-5",
    )

    assert result == {"product": "oracle-database", "versions": []}
    assert calls[0][0] == "https://api.openai.com/v1/responses"
    assert calls[0][1]["Authorization"] == "Bearer sk-test"
    assert calls[0][2]["model"] == "gpt-5"
    assert calls[0][3] == 60
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
.venv/bin/python -m pytest tests/python/test_openai_extract.py -q
```

Expected: FAIL with `ModuleNotFoundError: No module named 'pipeline.openai_extract'`.

- [ ] **Step 3: Implement OpenAI extraction client**

Create `pipeline/openai_extract.py`:

```python
import json
import os

import requests

OPENAI_RESPONSES_URL = "https://api.openai.com/v1/responses"
DEFAULT_MODEL = "gpt-5"


class OpenAIExtractionError(AssertionError):
    pass


AI_REFRESH_RESPONSE_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["product", "versions"],
    "properties": {
        "product": {"type": "string"},
        "versions": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["index", "record"],
                "properties": {
                    "index": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["label"],
                        "properties": {
                            "label": {"type": "string"},
                            "support_track": {"type": "string"},
                        },
                    },
                    "record": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": [
                            "product",
                            "version",
                            "release_label",
                            "record_type",
                            "released",
                            "sections",
                        ],
                        "properties": {
                            "product": {"type": "string"},
                            "version": {"type": "string"},
                            "release_label": {"type": "string"},
                            "record_type": {"type": "string", "enum": ["baseline", "release"]},
                            "released": {"type": "string"},
                            "sections": {
                                "type": "object",
                                "additionalProperties": False,
                                "required": [
                                    "certification",
                                    "whats_new",
                                    "behavior_changes",
                                    "deprecated",
                                    "desupported",
                                ],
                                "properties": {
                                    "certification": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "additionalProperties": False,
                                            "required": ["category", "value", "source_url"],
                                            "properties": {
                                                "category": {"type": "string"},
                                                "value": {"type": "string"},
                                                "source_url": {"type": "string"},
                                            },
                                        },
                                    },
                                    "whats_new": {"type": "array", "items": {"$ref": "#/$defs/feature"}},
                                    "behavior_changes": {"type": "array", "items": {"$ref": "#/$defs/feature"}},
                                    "deprecated": {"type": "array", "items": {"$ref": "#/$defs/feature"}},
                                    "desupported": {"type": "array", "items": {"$ref": "#/$defs/feature"}},
                                },
                            },
                        },
                    },
                },
            },
        },
    },
    "$defs": {
        "feature": {
            "type": "object",
            "additionalProperties": False,
            "required": ["title", "description", "source_url"],
            "properties": {
                "title": {"type": "string"},
                "description": {"type": "string"},
                "source_url": {"type": "string"},
            },
        }
    },
}


def require_openai_api_key(env=None):
    if env is None:
        env = os.environ
    api_key = env.get("OPENAI_API_KEY")
    if not api_key:
        raise OpenAIExtractionError("OPENAI_API_KEY is required for AI-assisted refresh")
    return api_key


def _page_block(page):
    content = " ".join(page.content.split())
    return f"URL: {page.url}\nCONTENT:\n{content[:12000]}"


def build_extraction_payload(product_id, product_label, existing_versions, pages, model=DEFAULT_MODEL):
    page_blocks = "\n\n---\n\n".join(_page_block(page) for page in pages)
    input_text = f"""Product id: {product_id}
Product label: {product_label}
Existing versions: {', '.join(existing_versions)}

Oracle source pages:
{page_blocks}
"""
    return {
        "model": model,
        "instructions": (
            "You extract Oracle Release Delta candidate records from Oracle-owned source pages. "
            "Return JSON only. Use only evidence from supplied Oracle-owned URLs. "
            "Every section item must include the exact Oracle source_url that supports it. "
            "Do not include non-Oracle URLs. Do not invent releases or dates."
        ),
        "input": input_text,
        "text": {
            "format": {
                "type": "json_schema",
                "name": "oracle_release_delta_candidates",
                "strict": True,
                "schema": AI_REFRESH_RESPONSE_SCHEMA,
            }
        },
    }


def parse_response_json(response_payload):
    for output in response_payload.get("output", []):
        for content in output.get("content", []):
            if content.get("type") == "refusal":
                raise OpenAIExtractionError(f"OpenAI refused extraction: {content.get('refusal', '')}")
            if content.get("type") == "output_text":
                return json.loads(content["text"])
    if response_payload.get("output_text"):
        return json.loads(response_payload["output_text"])
    raise OpenAIExtractionError("OpenAI response did not include output_text")


def extract_candidates(api_key, product_id, product_label, existing_versions, pages, post=None, model=DEFAULT_MODEL):
    post = post or requests.post
    payload = build_extraction_payload(product_id, product_label, existing_versions, pages, model=model)
    response = post(
        OPENAI_RESPONSES_URL,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=60,
    )
    response.raise_for_status()
    return parse_response_json(response.json())
```

- [ ] **Step 4: Run tests and commit**

```bash
.venv/bin/python -m pytest tests/python/test_openai_extract.py -q
git add tests/python/test_openai_extract.py pipeline/openai_extract.py
git commit -m "feat: add OpenAI extraction client"
```

Expected: tests pass.

## Task 3: AI Refresh Merge CLI

**Files:**
- Create: `tests/python/test_ai_refresh.py`
- Create: `pipeline/ai_refresh.py`

- [ ] **Step 1: Write failing AI refresh tests**

Create `tests/python/test_ai_refresh.py`:

```python
import json

import pytest

from pipeline.ai_refresh import (
    AIRefreshError,
    candidate_source_urls,
    merge_candidate_versions,
    run_ai_refresh,
    validate_candidate_payload,
)


def _source_definition():
    return {
        "product": {"id": "oracle-database", "label": "Oracle Database"},
        "versions": [
            {
                "index": {"label": "Oracle AI Database 26ai", "support_track": "Long Term Support Release"},
                "record": {
                    "product": "oracle-database",
                    "version": "26ai",
                    "release_label": "Oracle AI Database 26ai",
                    "record_type": "release",
                    "released": "2026-01-01",
                    "sections": {
                        "certification": [],
                        "whats_new": [],
                        "behavior_changes": [],
                        "deprecated": [],
                        "desupported": [],
                    },
                },
            }
        ],
    }


def _candidate_payload(version="27ai", source_url="https://docs.oracle.com/database/27ai"):
    return {
        "product": "oracle-database",
        "versions": [
            {
                "index": {"label": f"Oracle Database {version}"},
                "record": {
                    "product": "oracle-database",
                    "version": version,
                    "release_label": f"Oracle Database {version}",
                    "record_type": "release",
                    "released": "2027-01-01",
                    "sections": {
                        "certification": [],
                        "whats_new": [
                            {
                                "title": "New feature",
                                "description": "A sourced feature.",
                                "source_url": source_url,
                            }
                        ],
                        "behavior_changes": [],
                        "deprecated": [],
                        "desupported": [],
                    },
                },
            }
        ],
    }


def test_candidate_source_urls_collects_section_urls():
    urls = candidate_source_urls(_candidate_payload()["versions"][0]["record"])

    assert urls == ["https://docs.oracle.com/database/27ai"]


def test_validate_candidate_payload_rejects_wrong_product():
    payload = _candidate_payload()
    payload["product"] = "oracle-weblogic-server"

    with pytest.raises(AIRefreshError, match="product"):
        validate_candidate_payload(payload, "oracle-database", today="2026-05-31")


def test_validate_candidate_payload_rejects_non_oracle_source_url():
    payload = _candidate_payload(source_url="https://example.com/not-oracle")

    with pytest.raises(AIRefreshError, match="non-Oracle"):
        validate_candidate_payload(payload, "oracle-database", today="2026-05-31")


def test_merge_candidate_versions_adds_new_versions_newest_first():
    merged = merge_candidate_versions(_source_definition(), _candidate_payload()["versions"], today="2026-05-31")

    assert [entry["record"]["version"] for entry in merged["versions"]] == ["27ai", "26ai"]
    assert "last_updated" not in merged["versions"][0]["record"]
    assert merged["versions"][1]["index"]["support_track"] == "Long Term Support Release"


def test_merge_candidate_versions_replaces_existing_version_preserving_existing_index_metadata():
    payload = _candidate_payload(version="26ai")
    merged = merge_candidate_versions(_source_definition(), payload["versions"], today="2026-05-31")

    assert [entry["record"]["version"] for entry in merged["versions"]] == ["26ai"]
    assert merged["versions"][0]["index"] == {
        "label": "Oracle AI Database 26ai",
        "support_track": "Long Term Support Release",
    }
    assert merged["versions"][0]["record"]["sections"]["whats_new"][0]["title"] == "New feature"


def test_run_ai_refresh_requires_openai_key_before_file_writes(tmp_path):
    source_path = tmp_path / "oracle-database.json"
    source_path.write_text(json.dumps(_source_definition()), encoding="utf-8")

    with pytest.raises(AIRefreshError, match="OPENAI_API_KEY"):
        run_ai_refresh(
            products=["oracle-database"],
            source_paths={"oracle-database": source_path},
            targets={"oracle-database": {"label": "Oracle Database", "seed_urls": ["https://docs.oracle.com/database"]}},
            env={},
            discover=lambda seed_urls: [],
            extract=lambda **kwargs: _candidate_payload(),
            today="2026-05-31",
        )

    assert json.loads(source_path.read_text()) == _source_definition()


def test_run_ai_refresh_updates_curated_sources_not_data(tmp_path):
    source_path = tmp_path / "oracle-database.json"
    source_path.write_text(json.dumps(_source_definition()), encoding="utf-8")
    data_dir = tmp_path / "data"
    data_dir.mkdir()

    run_ai_refresh(
        products=["oracle-database"],
        source_paths={"oracle-database": source_path},
        targets={"oracle-database": {"label": "Oracle Database", "seed_urls": ["https://docs.oracle.com/database"]}},
        env={"OPENAI_API_KEY": "sk-test"},
        discover=lambda seed_urls: [],
        extract=lambda **kwargs: _candidate_payload(),
        today="2026-05-31",
    )

    updated = json.loads(source_path.read_text())
    assert [entry["record"]["version"] for entry in updated["versions"]] == ["27ai", "26ai"]
    assert list(data_dir.iterdir()) == []
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
.venv/bin/python -m pytest tests/python/test_ai_refresh.py -q
```

Expected: FAIL with `ModuleNotFoundError: No module named 'pipeline.ai_refresh'`.

- [ ] **Step 3: Implement AI refresh CLI**

Create `pipeline/ai_refresh.py`:

```python
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


def merge_candidate_versions(source_definition, candidate_versions, today):
    merged = copy.deepcopy(source_definition)
    existing_by_version = _entry_by_version(merged)
    for candidate in candidate_versions:
        record = copy.deepcopy(candidate["record"])
        record.pop("last_updated", None)
        _validate_record_without_last_updated(record, today)
        version = record["version"]
        existing_index = existing_by_version.get(version, {}).get("index", {})
        candidate_index = copy.deepcopy(candidate.get("index", {}))
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
    path.write_text(json.dumps(source_definition, indent=2), encoding="utf-8")


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
```

- [ ] **Step 4: Run tests and commit**

```bash
.venv/bin/python -m pytest tests/python/test_ai_refresh.py tests/python/test_openai_extract.py tests/python/test_oracle_discovery.py -q
git add tests/python/test_ai_refresh.py pipeline/ai_refresh.py
git commit -m "feat: merge AI refresh candidates into curated sources"
```

Expected: tests pass.

## Task 4: Manual GitHub Actions Workflow

**Files:**
- Create: `.github/workflows/ai-refresh-data.yml`
- Create: `tests/python/test_ai_refresh_workflow.py`

- [ ] **Step 1: Write failing workflow tests**

Create `tests/python/test_ai_refresh_workflow.py`:

```python
def _line_index(lines, expected):
    matches = [index for index, line in enumerate(lines) if line.strip() == expected]
    assert matches, f"Expected workflow line not found: {expected}"
    return matches[0]


def _contains_line(lines, expected):
    return any(line.strip() == expected for line in lines)


def test_ai_refresh_workflow_is_manual_only_and_uses_openai_secret(repo_root):
    workflow = (repo_root / ".github" / "workflows" / "ai-refresh-data.yml").read_text()
    lines = workflow.splitlines()

    assert "name: AI Assist Oracle Release Delta data" in workflow
    assert _contains_line(lines, "workflow_dispatch:")
    assert "schedule:" not in workflow
    assert "OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}" in workflow
    assert _contains_line(lines, "contents: write")
    assert _contains_line(lines, "pull-requests: write")


def test_ai_refresh_workflow_runs_ai_then_deterministic_build_then_tests(repo_root):
    workflow = (repo_root / ".github" / "workflows" / "ai-refresh-data.yml").read_text()
    lines = workflow.splitlines()

    ai_index = _line_index(lines, "run: .venv/bin/python -m pipeline.ai_refresh --products oracle-database oracle-weblogic-server")
    build_index = _line_index(lines, "run: .venv/bin/python -m pipeline.build")
    python_test_index = _line_index(lines, "run: .venv/bin/python -m pytest tests/python/ -q")
    js_test_index = _line_index(lines, "run: npm test")

    assert ai_index < build_index < python_test_index < js_test_index
    assert _contains_line(lines, "uses: peter-evans/create-pull-request@v6")
    assert _contains_line(lines, "commit-message: \"data: AI-assisted Oracle Release Delta refresh\"")
    assert _contains_line(lines, "branch: data/ai-refresh")
    assert _contains_line(lines, "title: \"AI data refresh: Oracle Release Delta\"")
    assert _contains_line(lines, "labels: data-refresh")
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
.venv/bin/python -m pytest tests/python/test_ai_refresh_workflow.py -q
```

Expected: FAIL with `FileNotFoundError` for `.github/workflows/ai-refresh-data.yml`.

- [ ] **Step 3: Add manual AI workflow**

Create `.github/workflows/ai-refresh-data.yml`:

```yaml
name: AI Assist Oracle Release Delta data

on:
  workflow_dispatch:

permissions:
  contents: write
  pull-requests: write

jobs:
  ai-refresh:
    runs-on: ubuntu-latest
    env:
      OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: |
          python -m pip install -r pipeline/requirements.txt
          python -m venv --system-site-packages .venv

      - name: Verify OpenAI API key
        run: |
          test -n "$OPENAI_API_KEY"

      - name: Run AI-assisted source refresh
        run: .venv/bin/python -m pipeline.ai_refresh --products oracle-database oracle-weblogic-server

      - name: Rebuild generated data
        run: .venv/bin/python -m pipeline.build

      - name: Run Python tests
        run: .venv/bin/python -m pytest tests/python/ -q

      - name: Run JavaScript tests
        run: npm test

      - name: Open pull request with AI-assisted data refresh
        uses: peter-evans/create-pull-request@v6
        with:
          commit-message: "data: AI-assisted Oracle Release Delta refresh"
          branch: data/ai-refresh
          title: "AI data refresh: Oracle Release Delta"
          body: |
            AI-assisted refresh of Oracle Release Delta curated source definitions.
            Review all Oracle source URLs and generated JSON before merging.
          labels: data-refresh
```

- [ ] **Step 4: Run tests and commit**

```bash
.venv/bin/python -m pytest tests/python/test_ai_refresh_workflow.py -q
git add .github/workflows/ai-refresh-data.yml tests/python/test_ai_refresh_workflow.py
git commit -m "ci: add manual AI-assisted data refresh workflow"
```

Expected: tests pass.

## Task 5: End-To-End Verification And Documentation

**Files:**
- Modify: `README.md`
- Modify: `docs/HANDOVER.md`
- Modify: `tests/python/test_ai_refresh_workflow.py`

- [ ] **Step 1: Add failing documentation checks**

Append to `tests/python/test_ai_refresh_workflow.py`:

```python
def test_docs_describe_manual_ai_refresh(repo_root):
    readme = (repo_root / "README.md").read_text()
    handover = (repo_root / "docs" / "HANDOVER.md").read_text()

    assert "AI Assist Oracle Release Delta data" in readme
    assert "OPENAI_API_KEY" in readme
    assert "manual-only" in readme
    assert "AI Assist Oracle Release Delta data" in handover
    assert "OPENAI_API_KEY" in handover
    assert "manual-only" in handover
```

- [ ] **Step 2: Run docs test to verify it fails**

```bash
.venv/bin/python -m pytest tests/python/test_ai_refresh_workflow.py::test_docs_describe_manual_ai_refresh -q
```

Expected: FAIL because README and handover do not yet describe the AI-assisted workflow.

- [ ] **Step 3: Update README**

In `README.md`, add this paragraph under the data refresh/update section:

```markdown
### AI-assisted data refresh

The `AI Assist Oracle Release Delta data` workflow is manual-only. It runs from
GitHub Actions, reads `OPENAI_API_KEY` from GitHub Actions secrets, asks OpenAI
to assist with Oracle Database and Oracle WebLogic Server curated-source updates,
then runs the deterministic `pipeline.build` step and opens a review PR. The
browser UI and deployed Vercel site never receive the OpenAI API key.
```

- [ ] **Step 4: Update handover**

In `docs/HANDOVER.md`, add this bullet near the pipeline/workflow current-state bullets:

```markdown
- GitHub Action `.github/workflows/ai-refresh-data.yml`: manual-only AI-assisted
  refresh for Oracle Database and Oracle WebLogic Server curated source
  definitions. It requires `OPENAI_API_KEY` in GitHub Actions secrets, updates
  `pipeline/curated_sources/`, runs `python -m pipeline.build`, and opens a
  review PR. The deployed Vercel site remains static and never receives the
  OpenAI API key.
```

- [ ] **Step 5: Run full verification**

```bash
.venv/bin/python -m pytest tests/python/ -q
npm test
.venv/bin/python -m pipeline.build
git diff --check
git status --short
```

Expected:

- Python tests pass.
- JS tests pass.
- Deterministic build exits `0`.
- `git diff --check` has no output.
- `git status --short` shows only planned workflow, docs, and AI pipeline files.

- [ ] **Step 6: Commit final docs and verification updates**

```bash
git add README.md docs/HANDOVER.md tests/python/test_ai_refresh_workflow.py
git commit -m "docs: document manual AI-assisted refresh"
```

Expected: commit succeeds.

## Final Verification

After all tasks are complete, run:

```bash
.venv/bin/python -m pytest tests/python/ -q
npm test
.venv/bin/python -m pipeline.build
.venv/bin/python - <<'PY'
import json
import pathlib
from pipeline.validate import validate_record

for path in pathlib.Path("data").glob("*/*.json"):
    validate_record(json.loads(path.read_text()))
print("validated data records")
PY
git diff --check
git status --short --branch
```

Expected:

- All Python tests pass.
- All JS tests pass.
- Deterministic build passes.
- Schema validation prints `validated data records`.
- `git diff --check` has no output.
- Worktree contains only committed changes or expected generated data diffs that are committed before PR update.
