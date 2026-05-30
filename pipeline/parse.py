import re

from bs4 import BeautifulSoup

def _text(node):
    return " ".join(node.get_text(" ", strip=True).split())


def release_version(label):
    """Derive a canonical version token from a release heading.

    "Release 26ai (23.26.1.0.0): January 2026" -> "23.26.1.0.0"
    "Release 23.10: January 2025"              -> "23.10"
    """
    m = re.search(r"\(([\d.]+)\)", label)
    if m:
        return m.group(1)
    m = re.search(r"Release\s+([0-9][0-9.]*)", label)
    if m:
        return m.group(1)
    return label.strip()


def parse_release_sections(html, source_url):
    """Parse an Oracle GoldenGate release-notes section page into per-release items.

    Each release is an `<h3 class="sect3">` heading. Items between one release
    heading and the next come in two layouts, both inside `div.section`:
      - `p.subhead2` (title) followed by a `<p>` (description)   — new-features / behavior
      - `dl > dt.dlterm` (title) with a `<dd>` (description)      — deprecated / desupported

    Returns a list (newest first, in document order) of:
        {"version": str, "label": str, "items": [{title, description, source_url}]}
    """
    soup = BeautifulSoup(html, "html.parser")
    releases = soup.find_all("h3", class_="sect3")
    results = []
    for h3 in releases:
        label = _text(h3)
        items = []
        for node in h3.find_all_next():
            if node is h3:
                continue
            if node.name == "h3" and "sect3" in (node.get("class") or []):
                break  # reached the next release
            if not getattr(node, "get", None):
                continue
            classes = node.get("class") or []
            if node.name == "p" and "subhead2" in classes:
                desc = node.find_next_sibling("p")
                items.append({
                    "title": _text(node),
                    "description": _text(desc) if desc else "",
                    "source_url": source_url,
                })
            elif node.name == "dt" and "dlterm" in classes:
                dd = node.find_next("dd")
                items.append({
                    "title": _text(node),
                    "description": _text(dd) if dd else "",
                    "source_url": source_url,
                })
        results.append({"version": release_version(label), "label": label, "items": items})
    return results

def parse_feature_list(html, source_url, heading="h3"):
    """Extract feature items: each `heading` is a title, the next <p> its description."""
    soup = BeautifulSoup(html, "html.parser")
    items = []
    for h in soup.find_all(heading):
        title = _text(h)
        if not title:
            continue
        desc_node = h.find_next("p")
        description = _text(desc_node) if desc_node else ""
        items.append({"title": title, "description": description, "source_url": source_url})
    return items

def parse_certification(html, source_url):
    """Extract certification rows from the first 2-column table body."""
    soup = BeautifulSoup(html, "html.parser")
    items = []
    table = soup.find("table")
    if not table:
        return items
    body = table.find("tbody") or table
    for row in body.find_all("tr"):
        cells = row.find_all("td")
        if len(cells) < 2:
            continue
        items.append({
            "category": _text(cells[0]),
            "value": _text(cells[1]),
            "source_url": source_url,
        })
    return items
