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
