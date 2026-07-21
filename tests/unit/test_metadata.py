from importlib import metadata

import pytest

import feed_sentiment
from feed_sentiment import _metadata
from feed_sentiment.feeds.retriever import RetrievalPolicy


def test_default_user_agent_matches_public_version() -> None:
    assert RetrievalPolicy().user_agent == (
        f"feed-sentiment/{feed_sentiment.__version__} "
        "(+https://github.com/kurtpatrickyu/feed-sentiment)"
    )


def test_custom_user_agent_override_is_unchanged() -> None:
    assert RetrievalPolicy(user_agent="custom-client/1.0").user_agent == "custom-client/1.0"


def test_missing_distribution_metadata_uses_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def missing(_name: str) -> str:
        raise metadata.PackageNotFoundError

    monkeypatch.setattr(metadata, "version", missing)
    assert _metadata.package_version() == _metadata.UNKNOWN_VERSION
    assert _metadata.default_user_agent() == (
        "feed-sentiment/0+unknown (+https://github.com/kurtpatrickyu/feed-sentiment)"
    )


def test_unexpected_metadata_failure_is_not_swallowed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def unexpected(_name: str) -> str:
        raise RuntimeError("metadata failure")

    monkeypatch.setattr(metadata, "version", unexpected)
    with pytest.raises(RuntimeError, match="metadata failure"):
        _metadata.package_version()
