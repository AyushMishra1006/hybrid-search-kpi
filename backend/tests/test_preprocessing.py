"""Unit tests for preprocessing utilities."""
import pytest

from app.utils.preprocessing import (
    MAX_DOC_WORDS,
    clean_text,
    highlight_snippet,
    truncate_long_doc,
)


class TestCleanText:
    def test_collapses_whitespace(self) -> None:
        assert clean_text("hello   world\t\nfoo") == "hello world foo"

    def test_strips_edges(self) -> None:
        assert clean_text("  hello  ") == "hello"

    def test_already_clean(self) -> None:
        assert clean_text("hello world") == "hello world"


class TestTruncateLongDoc:
    def test_short_doc_unchanged(self) -> None:
        text = "word " * 10
        result = truncate_long_doc(text.strip(), max_words=20)
        assert result == text.strip()

    def test_truncates_at_max_words(self) -> None:
        text = " ".join(str(i) for i in range(300))
        result = truncate_long_doc(text, max_words=256)
        assert len(result.split()) == 256

    def test_default_constant(self) -> None:
        text = " ".join("w" for _ in range(MAX_DOC_WORDS + 50))
        result = truncate_long_doc(text)
        assert len(result.split()) == MAX_DOC_WORDS

    def test_exact_boundary(self) -> None:
        text = " ".join("w" for _ in range(MAX_DOC_WORDS))
        result = truncate_long_doc(text)
        assert result == text


class TestHighlightSnippet:
    def test_wraps_matching_token(self) -> None:
        result = highlight_snippet("machine learning is great", "machine")
        assert "<em>machine</em>" in result

    def test_no_match_returns_start(self) -> None:
        result = highlight_snippet("hello world foo bar baz", "quantum", context_words=3)
        assert "hello" in result

    def test_multiple_tokens_highlighted(self) -> None:
        result = highlight_snippet("data science and machine learning", "data learning")
        assert "<em>data</em>" in result
        assert "<em>learning</em>" in result

    def test_empty_query_no_crash(self) -> None:
        result = highlight_snippet("some text here", "")
        assert isinstance(result, str)
