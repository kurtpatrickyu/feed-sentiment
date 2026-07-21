from __future__ import annotations

import socket
from pathlib import Path

import httpx
import pytest

from feed_sentiment.exceptions import (
    ContentTypeError,
    FeedFormatError,
    ResponseSizeError,
    RetrievalError,
    UnsafeUrlError,
)
from feed_sentiment.feeds.parser import parse_feed
from feed_sentiment.feeds.retriever import HttpxFeedRetriever, RetrievalPolicy, validate_url

FIXTURES = Path(__file__).parents[1] / "fixtures"


def test_parse_rss_normalizes_html_unicode_and_warnings() -> None:
    parsed = parse_feed((FIXTURES / "rss.xml").read_bytes())
    assert parsed.metadata.title == "Unicode News"
    assert len(parsed.entries) == 2
    assert parsed.entries[0].analysis_text == "Great launch 🚀\nUsers are very happy & excited."
    assert {warning.code for warning in parsed.warnings} == {"no_usable_text", "duplicate_entry"}


def test_parse_atom_and_empty_feed() -> None:
    atom = parse_feed((FIXTURES / "atom.xml").read_bytes())
    assert atom.entries[0].published_at is not None
    empty = parse_feed((FIXTURES / "empty.xml").read_bytes())
    assert empty.entries == ()
    assert empty.warnings[0].code == "empty_feed"


def test_malformed_feed_is_document_failure() -> None:
    with pytest.raises(FeedFormatError):
        parse_feed((FIXTURES / "malformed.xml").read_bytes())


def test_url_validation_rejects_credentials_and_private_dns(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with pytest.raises(UnsafeUrlError):
        validate_url("ftp://example.com/feed", RetrievalPolicy())
    with pytest.raises(UnsafeUrlError):
        validate_url("https://user:pass@example.com/feed", RetrievalPolicy())
    monkeypatch.setattr(
        socket,
        "getaddrinfo",
        lambda *args, **kwargs: [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 443))],
    )
    with pytest.raises(UnsafeUrlError):
        validate_url("https://example.com/feed", RetrievalPolicy())
    validate_url("https://example.com/feed", RetrievalPolicy(allow_private_networks=True))


def test_retriever_content_type_and_size(monkeypatch: pytest.MonkeyPatch) -> None:
    def html(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200, headers={"content-type": "text/html"}, content=b"<html/>", request=request
        )

    original = httpx.Client
    monkeypatch.setattr(
        httpx, "Client", lambda **kwargs: original(transport=httpx.MockTransport(html), **kwargs)
    )
    with pytest.raises(ContentTypeError):
        HttpxFeedRetriever().fetch(
            "https://example.com/feed", RetrievalPolicy(allow_private_networks=True)
        )


def test_retriever_size_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    original = httpx.Client
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            200, headers={"content-type": "application/rss+xml"}, content=b"12345", request=request
        )
    )
    monkeypatch.setattr(httpx, "Client", lambda **kwargs: original(transport=transport, **kwargs))
    with pytest.raises(ResponseSizeError):
        HttpxFeedRetriever().fetch(
            "https://example.com/feed",
            RetrievalPolicy(allow_private_networks=True, max_response_bytes=4),
        )


def test_retriever_maps_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    original = httpx.Client

    def timeout(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("slow", request=request)

    monkeypatch.setattr(
        httpx,
        "Client",
        lambda **kwargs: original(transport=httpx.MockTransport(timeout), **kwargs),
    )
    with pytest.raises(RetrievalError, match="timed out"):
        HttpxFeedRetriever().fetch(
            "https://example.com/feed", RetrievalPolicy(allow_private_networks=True)
        )
