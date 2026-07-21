from importlib.metadata import PackageNotFoundError, version
from typing import Any

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer  # type: ignore[import-untyped]

from feed_sentiment.analyzers.base import label_for
from feed_sentiment.models import AnalyzerMetadata, SentimentScore


def vader_version() -> str | None:
    try:
        return version("vaderSentiment")
    except PackageNotFoundError:
        return None


class VaderAnalyzer:
    def __init__(self, engine: Any | None = None) -> None:
        self._engine = engine or SentimentIntensityAnalyzer()

    def analyze(self, text: str) -> SentimentScore:
        raw = self._engine.polarity_scores(text)
        compound = float(raw["compound"])
        return SentimentScore(
            negative=float(raw["neg"]),
            neutral=float(raw["neu"]),
            positive=float(raw["pos"]),
            compound=compound,
            label=label_for(compound),
            analyzer=AnalyzerMetadata("vaderSentiment", vader_version()),
        )
