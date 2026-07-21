from __future__ import annotations

from collections.abc import Iterable

from feed_sentiment.analyzers import SentimentAnalyzer, VaderAnalyzer, label_for
from feed_sentiment.exceptions import AnalysisError, InputError
from feed_sentiment.feeds import FeedRetriever, HttpxFeedRetriever, RetrievalPolicy, parse_feed
from feed_sentiment.models import (
    AnalysisWarning,
    AnalyzedEntry,
    EntryAnalysisResult,
    FeedAnalysisSnapshot,
    NormalizedFeedEntry,
    SentimentScore,
    SnapshotAggregate,
    WarningCode,
)


def _analyzer(selected: SentimentAnalyzer | None) -> SentimentAnalyzer:
    return selected if selected is not None else VaderAnalyzer()


def analyze_text(text: str, *, analyzer: SentimentAnalyzer | None = None) -> SentimentScore:
    cleaned = text.strip()
    if not cleaned:
        raise InputError("Text must contain non-whitespace characters")
    try:
        return _analyzer(analyzer).analyze(cleaned)
    except AnalysisError:
        raise
    except Exception as exc:
        raise AnalysisError("Sentiment analyzer failed") from exc


def analyze_entries(
    entries: Iterable[NormalizedFeedEntry],
    *,
    analyzer: SentimentAnalyzer | None = None,
) -> EntryAnalysisResult:
    selected = _analyzer(analyzer)
    analyzed: list[AnalyzedEntry] = []
    warnings: list[AnalysisWarning] = []
    skipped = 0
    for index, entry in enumerate(entries):
        if not entry.analysis_text.strip():
            skipped += 1
            warnings.append(
                AnalysisWarning(
                    WarningCode.NO_USABLE_TEXT,
                    "Entry has no usable analysis text",
                    entry.identity,
                    index,
                )
            )
            continue
        try:
            analyzed.append(AnalyzedEntry(entry, selected.analyze(entry.analysis_text)))
        except Exception:
            skipped += 1
            warnings.append(
                AnalysisWarning(
                    WarningCode.ANALYSIS_FAILED,
                    "Sentiment analysis failed for entry",
                    entry.identity,
                    index,
                )
            )
    return EntryAnalysisResult(tuple(analyzed), tuple(warnings), skipped)


def aggregate_entries(
    entries: tuple[AnalyzedEntry, ...], skipped_count: int
) -> SnapshotAggregate | None:
    if not entries:
        return None
    count = len(entries)
    negative = sum(item.sentiment.negative for item in entries) / count
    neutral = sum(item.sentiment.neutral for item in entries) / count
    positive = sum(item.sentiment.positive for item in entries) / count
    compound = sum(item.sentiment.compound for item in entries) / count
    return SnapshotAggregate(
        negative, neutral, positive, compound, label_for(compound), count, skipped_count
    )


def analyze_feed(
    url: str,
    *,
    analyzer: SentimentAnalyzer | None = None,
    retriever: FeedRetriever | None = None,
    retrieval_policy: RetrievalPolicy | None = None,
) -> FeedAnalysisSnapshot:
    policy = retrieval_policy or RetrievalPolicy()
    fetched = (retriever or HttpxFeedRetriever()).fetch(url, policy)
    parsed = parse_feed(fetched.content)
    result = analyze_entries(parsed.entries, analyzer=analyzer)
    warnings = parsed.warnings + result.warnings
    skipped = parsed.source_entry_count - len(result.entries)
    return FeedAnalysisSnapshot(
        source_url=url,
        feed=parsed.metadata,
        entries=result.entries,
        warnings=warnings,
        snapshot_aggregate=aggregate_entries(result.entries, skipped),
    )
