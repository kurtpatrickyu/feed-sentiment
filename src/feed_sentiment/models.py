from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any, cast


class SentimentLabel(StrEnum):
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    POSITIVE = "positive"


class WarningCode(StrEnum):
    EMPTY_FEED = "empty_feed"
    NO_USABLE_TEXT = "no_usable_text"
    DUPLICATE_ENTRY = "duplicate_entry"
    INVALID_METADATA = "invalid_metadata"
    ANALYSIS_FAILED = "analysis_failed"


class WeightingMethod(StrEnum):
    EQUAL_ENTRY = "equal_entry"


class Serializable:
    def to_dict(self) -> dict[str, Any]:
        return cast(dict[str, Any], _json_value(asdict(cast(Any, self))))


def _json_value(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, StrEnum):
        return value.value
    if isinstance(value, dict):
        return {key: _json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_value(item) for item in value]
    return value


@dataclass(frozen=True, slots=True)
class AnalyzerMetadata(Serializable):
    name: str
    version: str | None


@dataclass(frozen=True, slots=True)
class SentimentScore(Serializable):
    negative: float
    neutral: float
    positive: float
    compound: float
    label: SentimentLabel
    analyzer: AnalyzerMetadata

    def __post_init__(self) -> None:
        for name in ("negative", "neutral", "positive"):
            if not 0.0 <= getattr(self, name) <= 1.0:
                raise ValueError(f"{name} must be between 0 and 1")
        if not -1.0 <= self.compound <= 1.0:
            raise ValueError("compound must be between -1 and 1")


@dataclass(frozen=True, slots=True)
class NormalizedFeedEntry(Serializable):
    identity: str
    entry_id: str | None
    url: str | None
    title: str | None
    summary: str | None
    published_at: datetime | None
    analysis_text: str


@dataclass(frozen=True, slots=True)
class AnalyzedEntry(Serializable):
    entry: NormalizedFeedEntry
    sentiment: SentimentScore


@dataclass(frozen=True, slots=True)
class AnalysisWarning(Serializable):
    code: WarningCode
    message: str
    entry_identity: str | None = None
    entry_index: int | None = None


@dataclass(frozen=True, slots=True)
class EntryAnalysisResult(Serializable):
    entries: tuple[AnalyzedEntry, ...]
    warnings: tuple[AnalysisWarning, ...]
    skipped_count: int


@dataclass(frozen=True, slots=True)
class SnapshotAggregate(Serializable):
    negative: float
    neutral: float
    positive: float
    compound: float
    label: SentimentLabel
    included_count: int
    skipped_count: int
    weighting: WeightingMethod = WeightingMethod.EQUAL_ENTRY


@dataclass(frozen=True, slots=True)
class FeedMetadata(Serializable):
    title: str | None = None
    url: str | None = None


@dataclass(frozen=True, slots=True)
class ParsedFeed(Serializable):
    metadata: FeedMetadata
    entries: tuple[NormalizedFeedEntry, ...]
    warnings: tuple[AnalysisWarning, ...]
    source_entry_count: int


@dataclass(frozen=True, slots=True)
class FeedAnalysisSnapshot(Serializable):
    source_url: str
    feed: FeedMetadata
    entries: tuple[AnalyzedEntry, ...]
    warnings: tuple[AnalysisWarning, ...]
    snapshot_aggregate: SnapshotAggregate | None
