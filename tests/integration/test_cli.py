from __future__ import annotations

import importlib
import json
from typing import NoReturn

import pytest
from typer.testing import CliRunner

from feed_sentiment import __version__
from feed_sentiment.cli.app import app
from feed_sentiment.exceptions import RetrievalError
from feed_sentiment.models import AnalysisWarning, FeedAnalysisSnapshot, FeedMetadata, WarningCode

runner = CliRunner()
cli_module = importlib.import_module("feed_sentiment.cli.app")


def empty_snapshot() -> FeedAnalysisSnapshot:
    return FeedAnalysisSnapshot(
        "https://example.com/feed",
        FeedMetadata("Empty", None),
        (),
        (AnalysisWarning(WarningCode.EMPTY_FEED, "Feed contains no entries"),),
        None,
    )


def test_help_and_version_do_not_analyze() -> None:
    assert runner.invoke(app, ["--help"]).exit_code == 0
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert result.stdout.strip() == __version__


def test_json_is_clean_and_unicode(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cli_module, "analyze_feed", lambda url: empty_snapshot())
    result = runner.invoke(app, ["analyze", "https://example.com/feed", "--format", "json"])
    assert result.exit_code == 0
    assert json.loads(result.stdout)["snapshot_aggregate"] is None
    assert result.stderr == ""


def test_expected_failure_uses_stderr_and_exit_one(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail(url: str) -> NoReturn:
        raise RetrievalError(url, "unreachable")

    monkeypatch.setattr(cli_module, "analyze_feed", fail)
    result = runner.invoke(app, ["analyze", "https://example.com/feed"])
    assert result.exit_code == 1
    assert result.stdout == ""
    assert "unreachable" in result.stderr
    assert "Traceback" not in result.stderr


def test_invalid_format_is_usage_error() -> None:
    result = runner.invoke(app, ["analyze", "https://example.com/feed", "--format", "yaml"])
    assert result.exit_code == 2
