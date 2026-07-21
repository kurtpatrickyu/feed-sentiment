from __future__ import annotations

from pathlib import Path

from feed_sentiment import RetrievalPolicy, analyze_feed
from feed_sentiment.feeds.retriever import RetrievedFeed
from feed_sentiment.models import AnalyzerMetadata, SentimentLabel, SentimentScore

FIXTURES = Path(__file__).parents[1] / "fixtures"


class FixtureRetriever:
    def __init__(self, name: str) -> None:
        self.name = name

    def fetch(self, url: str, policy: RetrievalPolicy) -> RetrievedFeed:
        return RetrievedFeed(url, (FIXTURES / self.name).read_bytes(), "application/xml")


class LengthAnalyzer:
    def analyze(self, text: str) -> SentimentScore:
        compound = 0.5 if "happy" in text else -0.5
        label = SentimentLabel.POSITIVE if compound > 0 else SentimentLabel.NEGATIVE
        return SentimentScore(0.2, 0.3, 0.5, compound, label, AnalyzerMetadata("fixture", "1"))


def test_public_feed_snapshot_and_aggregate() -> None:
    snapshot = analyze_feed(
        "https://example.com/rss", analyzer=LengthAnalyzer(), retriever=FixtureRetriever("rss.xml")
    )
    assert len(snapshot.entries) == 2
    assert snapshot.snapshot_aggregate is not None
    assert snapshot.snapshot_aggregate.compound == 0.0
    assert snapshot.snapshot_aggregate.label is SentimentLabel.NEUTRAL
    assert snapshot.snapshot_aggregate.included_count == 2
    assert snapshot.snapshot_aggregate.skipped_count == 2
    assert snapshot.to_dict()["snapshot_aggregate"]["weighting"] == "equal_entry"


def test_empty_feed_is_success_with_null_aggregate() -> None:
    snapshot = analyze_feed(
        "https://example.com/empty",
        analyzer=LengthAnalyzer(),
        retriever=FixtureRetriever("empty.xml"),
    )
    assert snapshot.entries == ()
    assert snapshot.snapshot_aggregate is None
    assert snapshot.warnings[0].code == "empty_feed"
