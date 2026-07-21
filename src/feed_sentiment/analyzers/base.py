from typing import Protocol

from feed_sentiment.models import SentimentLabel, SentimentScore


class SentimentAnalyzer(Protocol):
    def analyze(self, text: str) -> SentimentScore: ...


def label_for(compound: float) -> SentimentLabel:
    if compound >= 0.05:
        return SentimentLabel.POSITIVE
    if compound <= -0.05:
        return SentimentLabel.NEGATIVE
    return SentimentLabel.NEUTRAL
