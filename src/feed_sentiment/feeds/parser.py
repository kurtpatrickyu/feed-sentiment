from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from time import struct_time
from typing import Any

import feedparser  # type: ignore[import-untyped]
from bs4 import BeautifulSoup

from feed_sentiment.exceptions import FeedFormatError
from feed_sentiment.models import (
    AnalysisWarning,
    FeedMetadata,
    NormalizedFeedEntry,
    ParsedFeed,
    WarningCode,
)


def _clean(value: Any) -> str | None:
    if value is None:
        return None
    cleaned = " ".join(str(value).split())
    return cleaned or None


def html_to_text(value: Any) -> str | None:
    if value is None:
        return None
    soup = BeautifulSoup(str(value), "html.parser")
    for element in soup(["script", "style"]):
        element.decompose()
    return _clean(soup.get_text(" "))


def construct_analysis_text(title: str | None, summary: str | None) -> str:
    return "\n".join(part for part in (title, summary) if part)


def _timestamp(entry: Any) -> tuple[datetime | None, bool]:
    value: struct_time | None = entry.get("published_parsed") or entry.get("updated_parsed")
    if value is None:
        raw_present = bool(entry.get("published") or entry.get("updated"))
        return None, raw_present
    try:
        return datetime(*value[:6], tzinfo=UTC), False
    except (TypeError, ValueError, OverflowError):
        return None, True


def _identity(
    entry_id: str | None,
    url: str | None,
    title: str | None,
    summary: str | None,
    published_at: datetime | None,
) -> str:
    if entry_id:
        return f"id:{entry_id}"
    if url:
        return f"url:{url}"
    payload = "\x1f".join(
        (title or "", summary or "", published_at.isoformat() if published_at else "")
    )
    return f"sha256:{hashlib.sha256(payload.encode('utf-8')).hexdigest()}"


def parse_feed(content: bytes) -> ParsedFeed:
    parsed = feedparser.parse(content)
    if not parsed.get("version") or parsed.get("bozo"):
        detail = str(parsed.get("bozo_exception", "unrecognized RSS or Atom document"))
        raise FeedFormatError(f"Malformed feed document: {detail}")

    warnings: list[AnalysisWarning] = []
    normalized: list[NormalizedFeedEntry] = []
    seen: set[str] = set()
    raw_entries = parsed.get("entries", ())
    for index, raw in enumerate(raw_entries):
        entry_id = _clean(raw.get("id") or raw.get("guid"))
        url = _clean(raw.get("link"))
        title = _clean(raw.get("title"))
        summary_source = raw.get("summary")
        if summary_source is None and raw.get("content"):
            summary_source = raw["content"][0].get("value")
        summary = html_to_text(summary_source)
        published_at, invalid_date = _timestamp(raw)
        identity = _identity(entry_id, url, title, summary, published_at)
        if invalid_date:
            warnings.append(
                AnalysisWarning(
                    WarningCode.INVALID_METADATA,
                    "Invalid publication date was omitted",
                    identity,
                    index,
                )
            )
        text = construct_analysis_text(title, summary)
        if not text:
            warnings.append(
                AnalysisWarning(
                    WarningCode.NO_USABLE_TEXT,
                    "Entry has no usable title or summary",
                    identity,
                    index,
                )
            )
            continue
        if identity in seen:
            warnings.append(
                AnalysisWarning(
                    WarningCode.DUPLICATE_ENTRY, "Duplicate entry was skipped", identity, index
                )
            )
            continue
        seen.add(identity)
        normalized.append(
            NormalizedFeedEntry(identity, entry_id, url, title, summary, published_at, text)
        )

    if not raw_entries:
        warnings.append(AnalysisWarning(WarningCode.EMPTY_FEED, "Feed contains no entries"))
    feed = parsed.get("feed", {})
    metadata = FeedMetadata(_clean(feed.get("title")), _clean(feed.get("link")))
    return ParsedFeed(metadata, tuple(normalized), tuple(warnings), len(raw_entries))
