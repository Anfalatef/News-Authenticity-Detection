"""
Chunking strategy for evidence retrieval.

We chunk by paragraphs grouped into roughly max_words to keep semantic coherence.
"""

from __future__ import annotations


def chunk_by_paragraphs(text: str, max_words: int = 220) -> list[str]:
    paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
    chunks: list[str] = []
    buf: list[str] = []
    word_count = 0

    for p in paragraphs:
        words = p.split()
        w = len(words)

        # If a paragraph is too long, split it into word blocks.
        if w > int(max_words * 1.5):
            if buf:
                chunks.append(" ".join(buf).strip())
                buf, word_count = [], 0

            step = max_words
            for i in range(0, w, step):
                part = " ".join(words[i:i + step]).strip()
                if part:
                    chunks.append(part)
            continue

        if word_count + w <= max_words:
            buf.append(p)
            word_count += w
        else:
            if buf:
                chunks.append(" ".join(buf).strip())
            buf = [p]
            word_count = w

    if buf:
        chunks.append(" ".join(buf).strip())

    # Keep only meaningful chunks
    return [c for c in chunks if len(c) >= 120]
