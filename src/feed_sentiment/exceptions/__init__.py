class FeedSentimentError(Exception):
    """Base exception for expected package failures."""


class InputError(FeedSentimentError, ValueError):
    """Raised when caller input cannot be analyzed."""


class AnalysisError(FeedSentimentError):
    """Raised when a sentiment analyzer fails."""


class RetrievalError(FeedSentimentError):
    """Raised when a feed cannot be retrieved."""

    def __init__(self, url: str, message: str) -> None:
        self.url = url
        super().__init__(f"{message}: {url}")


class UnsafeUrlError(RetrievalError):
    """Raised when URL policy rejects a destination."""


class ResponseSizeError(RetrievalError):
    """Raised when a response exceeds its byte limit."""


class ContentTypeError(RetrievalError):
    """Raised for a clearly incompatible response media type."""


class FeedFormatError(FeedSentimentError):
    """Raised when content is not a recognizable RSS or Atom document."""
