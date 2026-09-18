from bs4 import BeautifulSoup
import re


REMOVE_TAGS = [
    "script",
    "style",
    "noscript",
    "svg",
    "canvas",
    "iframe",
    "template",
    "form",
]

REMOVE_SELECTORS = [
    "nav",
    "footer",
    "header",
    "[role='navigation']",
    "[role='banner']",
    "[role='contentinfo']",
    ".cookie",
    ".cookies",
    ".cookie-banner",
    ".cookie-consent",
    ".privacy-banner",
    ".gdpr",
    ".advertisement",
    ".ads",
    ".modal",
    ".popup",
]


def clean_html(html: str) -> str:
    """Convert raw HTML into clean, LLM-friendly text."""

    if not html:
        return ""

    soup = BeautifulSoup(html, "html.parser")

    # Remove unwanted tags
    for tag_name in REMOVE_TAGS:
        for tag in soup.find_all(tag_name):
            tag.decompose()

    # Remove navigation, footer, cookie banners, ads, etc.
    for selector in REMOVE_SELECTORS:
        for element in soup.select(selector):
            element.decompose()

    # Prefer the main content when available
    main = soup.find("main")

    if main:
        text = main.get_text("\n", strip=True)
    else:
        body = soup.find("body")
        text = body.get_text("\n", strip=True) if body else soup.get_text("\n", strip=True)

    # Remove common cookie/privacy boilerplate
    boilerplate_patterns = [
        r"this website uses cookies.*",
        r"we use cookies.*",
        r"accept cookies.*",
        r"cookie settings.*",
        r"privacy policy.*advertising.*",
        r"by continuing to browse.*",
        r"manage cookies.*",
    ]

    for pattern in boilerplate_patterns:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE | re.DOTALL)

    # Normalize whitespace
    lines = []

    for line in text.splitlines():
        line = re.sub(r"\s+", " ", line).strip()

        if not line:
            continue

        # Remove extremely short UI fragments
        if len(line) <= 2:
            continue

        lines.append(line)

    text = "\n".join(lines)

    # Remove repeated lines
    seen = set()
    unique_lines = []

    for line in text.splitlines():
        normalized = line.lower()

        if normalized not in seen:
            seen.add(normalized)
            unique_lines.append(line)

    return "\n".join(unique_lines)