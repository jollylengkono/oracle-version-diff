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


def oracle_source_url(url):
    parsed = urlparse(url)
    return parsed.scheme == "https" and oracle_owned_url(url)


def require_oracle_url(url):
    if not oracle_owned_url(url):
        raise OracleSourceError(f"non-Oracle URL rejected: {url}")
    return url


def require_oracle_source_url(url):
    if not oracle_source_url(url):
        raise OracleSourceError(f"HTTPS Oracle URL required: {url}")
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
    require_oracle_source_url(url)
    session = session or requests.Session()
    response = session.get(
        url,
        timeout=30,
        headers={"User-Agent": USER_AGENT},
        allow_redirects=True,
    )
    response.raise_for_status()
    final_url = response.url or url
    redirect_urls = [hop.url for hop in getattr(response, "history", []) if hop.url]
    for redirect_url in redirect_urls + [final_url]:
        if not oracle_source_url(redirect_url):
            raise OracleSourceError(f"Oracle URL redirected to non-HTTPS Oracle URL: {redirect_url}")
    return OraclePage(final_url, response.text)


def _candidate_links(page):
    soup = BeautifulSoup(page.content, "html.parser")
    hrefs = [a.get("href") for a in soup.find_all("a") if a.get("href")]
    urls = unique_oracle_urls(hrefs, page.url)
    return [
        url for url in urls
        if oracle_source_url(url) and any(hint in url.lower() for hint in LINK_HINTS)
    ]


def discover_oracle_pages(seed_urls, session=None, max_linked_pages=12):
    pages = []
    linked_urls = []
    seen_urls = set()
    for seed_url in seed_urls:
        if seed_url in seen_urls:
            continue
        seen_urls.add(seed_url)
        seed_page = fetch_oracle_page(seed_url, session=session)
        pages.append(seed_page)
        seen_urls.add(seed_page.url)
        for linked_url in _candidate_links(seed_page):
            if linked_url in seen_urls:
                continue
            seen_urls.add(linked_url)
            linked_urls.append(linked_url)
    for url in linked_urls[:max_linked_pages]:
        pages.append(fetch_oracle_page(url, session=session))
    return pages


def load_ai_source_targets(path):
    targets = json.loads(path.read_text(encoding="utf-8"))
    for product_id, target in targets.items():
        if not target.get("label"):
            raise OracleSourceError(f"AI source target missing label: {product_id}")
        seed_urls = target.get("seed_urls")
        if not isinstance(seed_urls, list) or not seed_urls:
            raise OracleSourceError(f"AI source target missing seed_urls list: {product_id}")
        for url in seed_urls:
            require_oracle_source_url(url)
    return targets
