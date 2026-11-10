"""
Article text extraction from HTML.

This is a generic extractor:
- Removes scripts/styles/nav/ads-like sections
- Prefers <article> content if available
- Falls back to all <p> tags
"""

from __future__ import annotations

from bs4 import BeautifulSoup


def extract_title_and_text(html: str) -> tuple[str, str]:
    soup = BeautifulSoup(html, "html.parser")

    # Title: prefer <meta property="og:title"> then <title>
    title = ""
    og_title = soup.find("meta", attrs={"property": "og:title"})
    if og_title and og_title.get("content"):
        title = og_title["content"].strip()
    elif soup.title and soup.title.get_text(strip=True):
        title = soup.title.get_text(strip=True)

    # Remove common non-content
    for tag in soup(["script", "style", "noscript", "header", "footer", "nav", "aside", "form"]):
        tag.decompose()

    # Prefer <article> if present
    article = soup.find("article")
    if article:
        paragraphs = [p.get_text(" ", strip=True) for p in article.find_all("p")]
    else:
        paragraphs = [p.get_text(" ", strip=True) for p in soup.find_all("p")]

    # Keep only meaningful paragraphs
    cleaned = [p for p in paragraphs if p and len(p) >= 30]
    text = "\n".join(cleaned).strip()

    return title, text
