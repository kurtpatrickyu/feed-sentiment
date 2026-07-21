from __future__ import annotations

from datetime import UTC, datetime

import pytest

from feed_sentiment import (
    AnalysisError,
    InputError,
    NormalizedFeedEntry,
    analyze_entries,
    analyze_text,
)
from feed_sentiment.analyzers.base import label_for
from feed_sentiment.models import AnalyzerMetadata, SentimentLabel, SentimentScore
from feed_sentiment.services.analysis import aggregate_entries


class FakeAnalyzer:
    def analyze(self, text: str) -> SentimentScore:
        if text == "fail":
            raise RuntimeError("boom")
        compound = 0.5 if "good" in text else -0.5
        return SentimentScore(
            0.1, 0.2, 0.7, compound, label_for(compound), AnalyzerMetadata("fake", "1")
        )


def entry(identity: str, text: str) -> NormalizedFeedEntry:
    return NormalizedFeedEntry(
        identity, identity, None, text, None, datetime(2026, 1, 1, tzinfo=UTC), text
    )


@pytest.mark.parametrize(
    ("compound", "label"),
    [
        (-0.05, SentimentLabel.NEGATIVE),
        (-0.049, SentimentLabel.NEUTRAL),
        (0.049, SentimentLabel.NEUTRAL),
        (0.05, SentimentLabel.POSITIVE),
    ],
)
def test_label_boundaries(compound: float, label: SentimentLabel) -> None:
    assert label_for(compound) is label


def test_score_validates_ranges() -> None:
    with pytest.raises(ValueError):
        SentimentScore(1.1, 0, 0, 0, SentimentLabel.NEUTRAL, AnalyzerMetadata("x", None))


def test_analyze_text_custom_and_empty() -> None:
    assert analyze_text(" good ", analyzer=FakeAnalyzer()).label is SentimentLabel.POSITIVE
    with pytest.raises(InputError):
        analyze_text("   ", analyzer=FakeAnalyzer())


def test_analyze_text_chains_analyzer_failure() -> None:
    with pytest.raises(AnalysisError) as caught:
        analyze_text("fail", analyzer=FakeAnalyzer())
    assert isinstance(caught.value.__cause__, RuntimeError)


def test_entries_partial_failure_and_aggregate() -> None:
    result = analyze_entries([entry("1", "good"), entry("2", "fail")], analyzer=FakeAnalyzer())
    assert len(result.entries) == 1
    assert result.skipped_count == 1
    assert result.warnings[0].code == "analysis_failed"
    aggregate = aggregate_entries(result.entries, result.skipped_count)
    assert aggregate is not None
    assert aggregate.included_count == 1
    assert aggregate.skipped_count == 1
    assert aggregate.weighting == "equal_entry"


def test_empty_aggregate_is_none() -> None:
    assert aggregate_entries((), 3) is None
