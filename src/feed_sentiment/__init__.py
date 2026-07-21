from feed_sentiment._metadata import package_version
from feed_sentiment.exceptions import (
    AnalysisError,
    ContentTypeError,
    FeedFormatError,
    FeedSentimentError,
    InputError,
    ResponseSizeError,
    RetrievalError,
    UnsafeUrlError,
)
from feed_sentiment.feeds import FeedRetriever, RetrievalPolicy
from feed_sentiment.models import (
    AnalysisWarning,
    AnalyzedEntry,
    AnalyzerMetadata,
    EntryAnalysisResult,
    FeedAnalysisSnapshot,
    FeedMetadata,
    NormalizedFeedEntry,
    SentimentLabel,
    SentimentScore,
    SnapshotAggregate,
    WarningCode,
    WeightingMethod,
)
from feed_sentiment.services import analyze_entries, analyze_feed, analyze_text

__version__ = package_version()

__all__ = [
    "AnalysisError",
    "AnalysisWarning",
    "AnalyzerMetadata",
    "AnalyzedEntry",
    "ContentTypeError",
    "EntryAnalysisResult",
    "FeedAnalysisSnapshot",
    "FeedFormatError",
    "FeedMetadata",
    "FeedRetriever",
    "FeedSentimentError",
    "InputError",
    "NormalizedFeedEntry",
    "ResponseSizeError",
    "RetrievalError",
    "RetrievalPolicy",
    "SentimentLabel",
    "SentimentScore",
    "SnapshotAggregate",
    "UnsafeUrlError",
    "WarningCode",
    "WeightingMethod",
    "__version__",
    "analyze_entries",
    "analyze_feed",
    "analyze_text",
]
