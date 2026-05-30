import re
from bs4 import BeautifulSoup

# Matches "Oracle GoldenGate 23ai" / "... 21c" / "... 19c" and captures the version token.
_VER_RE = re.compile(r"Oracle GoldenGate\s+(\d+[a-z]+)", re.IGNORECASE)

def detect_versions(html):
    """Return version tokens (e.g. '23ai') in document order, de-duplicated."""
    soup = BeautifulSoup(html, "html.parser")
    seen = []
    for a in soup.find_all("a"):
        m = _VER_RE.search(a.get_text(" ", strip=True))
        if m and m.group(1) not in seen:
            seen.append(m.group(1))
    return seen
