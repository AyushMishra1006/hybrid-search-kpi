"""Text preprocessing utilities shared by ingest, search, and eval."""
from __future__ import annotations

import re

MAX_DOC_WORDS: int = 300


def clean_text(text: str) -> str:
    """Collapse all whitespace runs to single spaces and strip edges."""
    return re.sub(r"\s+", " ", text).strip()


def truncate_long_doc(text: str, max_words: int = MAX_DOC_WORDS) -> str:
    """Return at most max_words words joined by spaces."""
    words = text.split()
    if len(words) <= max_words:
        return text
    return " ".join(words[:max_words])


def highlight_snippet(text: str, query: str, context_words: int = 20) -> str:
    """
    Return a snippet of up to context_words words centred on the first query
    term match, with matched tokens wrapped in <em>...</em>.
    Falls back to the first context_words words if no match.
    """
    words = text.split()
    query_tokens = {t.lower() for t in query.split() if t}

    match_idx = next(
        (i for i, w in enumerate(words) if re.sub(r"[^a-z0-9]", "", w.lower()) in query_tokens),
        None,
    )

    if match_idx is None:
        snippet_words = words[:context_words]
    else:
        half = context_words // 2
        start = max(0, match_idx - half)
        end = min(len(words), start + context_words)
        snippet_words = words[start:end]

    highlighted = [
        f"<em>{w}</em>" if re.sub(r"[^a-z0-9]", "", w.lower()) in query_tokens else w
        for w in snippet_words
    ]
    return " ".join(highlighted) + ("..." if len(words) > context_words else "")
