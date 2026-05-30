from bs4 import BeautifulSoup

def _text(node):
    return " ".join(node.get_text(" ", strip=True).split())

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
