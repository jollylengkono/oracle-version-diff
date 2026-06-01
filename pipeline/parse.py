import re

from bs4 import BeautifulSoup

_MONTHS = {
    "january": "01",
    "february": "02",
    "march": "03",
    "april": "04",
    "may": "05",
    "june": "06",
    "july": "07",
    "august": "08",
    "september": "09",
    "october": "10",
    "november": "11",
    "december": "12",
}

def _text(node):
    return " ".join(node.get_text(" ", strip=True).split())


def _section_level(node):
    if not getattr(node, "get", None):
        return None
    for cls in node.get("class") or []:
        m = re.fullmatch(r"sect(\d+)", cls)
        if m:
            return int(m.group(1))
    if node.name and re.fullmatch(r"h[1-6]", node.name):
        return int(node.name[1])
    return None


def _is_section_heading(node):
    return _section_level(node) is not None


def _is_release_heading(node):
    return _is_section_heading(node) and "Release" in _text(node)


def release_version(label):
    """Derive a canonical version token from a release heading.

    "Release 26ai (23.26.1.0.0): January 2026" -> "23.26.1.0.0"
    "Release 23.10: January 2025"              -> "23.10"
    """
    m = re.search(r"\(([\d.]+)\)", label)
    if m:
        return m.group(1)
    m = re.search(r"Release\s+\S+\s+\(([\d.]+)\)", label)
    if m:
        return m.group(1)
    m = re.search(r"Release\s+([0-9][0-9.]*)", label)
    if m:
        return m.group(1)
    return label.strip()


def release_date(label):
    """Extract an ISO month-start release date from a release heading."""
    m = re.search(
        r"\b("
        + "|".join(_MONTHS)
        + r")\s+((?:19|20)\d{2})\b",
        label,
        re.IGNORECASE,
    )
    if not m:
        return None
    return f"{m.group(2)}-{_MONTHS[m.group(1).lower()]}-01"


def parse_release_sections(html, source_url, section_title=None):
    """Parse an Oracle GoldenGate release-notes section page into per-release items.

    Each release is a section heading. Items between one release
    heading and the next come in two layouts, both inside `div.section`:
      - `p.subhead2` (title) followed by a `<p>` (description)   — new-features / behavior
      - `dl > dt.dlterm` (title) with a `<dd>` (description)      — deprecated / desupported

    Returns a list (newest first, in document order) of:
        {"version": str, "label": str, "released": str, "items": [{title, description, source_url}]}
    """
    soup = BeautifulSoup(html, "html.parser")
    scope_start = None
    scope_level = None
    if section_title:
        for node in soup.find_all(["h2", "h3", "h4"]):
            if _is_release_heading(node):
                continue
            if section_title.lower() in _text(node).lower():
                scope_start = node
                scope_level = _section_level(node)
                break

    releases = []
    headings = (
        scope_start.find_all_next(["h2", "h3", "h4"])
        if scope_start
        else soup.find_all(["h2", "h3", "h4"])
    )
    for node in headings:
        if scope_start and node is scope_start:
            continue
        if scope_start and not _is_release_heading(node) and _section_level(node) is not None:
            if _section_level(node) <= scope_level:
                break
        if _is_release_heading(node):
            releases.append(node)
    results = []
    for h3 in releases:
        label = _text(h3)
        parse_bold_paragraph_items = h3.name == "h2"
        release_level = _section_level(h3)
        items = []
        for node in h3.find_all_next():
            if node is h3:
                continue
            node_level = _section_level(node)
            if node_level is not None:
                if scope_start and node_level <= scope_level and not _is_release_heading(node):
                    break  # reached the next selected section
                if _is_release_heading(node) and node_level <= release_level:
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
                title = _text(node)
                dd = node.find_next_sibling("dd")
                if title and not (dd and dd.find("dt", class_="dlterm")):
                    items.append({
                        "title": title,
                        "description": _text(dd) if dd else "",
                        "source_url": source_url,
                    })
            elif parse_bold_paragraph_items and node.name == "p" and node.find("span", class_="bold"):
                desc = node.find_next_sibling("p")
                items.append({
                    "title": _text(node),
                    "description": _text(desc) if desc else "",
                    "source_url": source_url,
                })
        results.append({
            "version": release_version(label),
            "label": label,
            "released": release_date(label),
            "items": items,
        })
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
