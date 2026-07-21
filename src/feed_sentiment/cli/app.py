from __future__ import annotations

import json
from enum import StrEnum
from typing import Annotated

import typer

from feed_sentiment import RetrievalPolicy, __version__, analyze_feed
from feed_sentiment.exceptions import FeedSentimentError
from feed_sentiment.models import FeedAnalysisSnapshot

app = typer.Typer(
    no_args_is_help=True, add_completion=False, help="Analyze RSS and Atom sentiment snapshots."
)


class OutputFormat(StrEnum):
    TEXT = "text"
    JSON = "json"


def _version(value: bool) -> None:
    if value:
        typer.echo(__version__)
        raise typer.Exit()


@app.callback()
def main(
    version: Annotated[
        bool,
        typer.Option(
            "--version", callback=_version, is_eager=True, help="Show the installed version."
        ),
    ] = False,
) -> None:
    """Analyze RSS and Atom sentiment snapshots."""


def render_text(snapshot: FeedAnalysisSnapshot) -> str:
    lines = [f"Feed: {snapshot.feed.title or snapshot.source_url}"]
    for item in snapshot.entries:
        name = item.entry.title or item.entry.identity
        lines.append(f"- {name}: {item.sentiment.label} ({item.sentiment.compound:.4f})")
    aggregate = snapshot.snapshot_aggregate
    if aggregate is None:
        lines.append("Snapshot aggregate: none (no successfully analyzed entries)")
    else:
        lines.append(
            f"Snapshot aggregate: {aggregate.label} ({aggregate.compound:.4f}); "
            f"included={aggregate.included_count}, skipped={aggregate.skipped_count}, "
            f"weighting={aggregate.weighting}"
        )
    for warning in snapshot.warnings:
        lines.append(f"Warning [{warning.code}]: {warning.message}")
    return "\n".join(lines)


@app.command()
def analyze(
    feed_url: Annotated[str, typer.Argument(help="HTTP(S) RSS or Atom URL.")],
    output_format: Annotated[
        OutputFormat, typer.Option("--format", case_sensitive=False)
    ] = OutputFormat.TEXT,
    allow_private_network: Annotated[
        bool,
        typer.Option(
            "--allow-private-network",
            help="Explicitly allow trusted private-network feed destinations.",
        ),
    ] = False,
) -> None:
    """Analyze one feed snapshot."""
    try:
        if allow_private_network:
            snapshot = analyze_feed(
                feed_url,
                retrieval_policy=RetrievalPolicy(allow_private_networks=True),
            )
        else:
            snapshot = analyze_feed(feed_url)
    except FeedSentimentError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(1) from exc
    if output_format is OutputFormat.JSON:
        typer.echo(json.dumps(snapshot.to_dict(), ensure_ascii=True))
    else:
        typer.echo(render_text(snapshot))


if __name__ == "__main__":
    app()
