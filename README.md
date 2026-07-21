# Feed Sentiment

Feed Sentiment is an MIT-licensed Python 3.12+ package for one-shot sentiment analysis of RSS and Atom feed snapshots. It normalizes entries, scores each usable entry with VADER, and returns an explicitly defined snapshot aggregate.

## Installation

```console
python -m pip install feed-sentiment
```

Runtime dependencies have narrow roles: `httpx` performs bounded HTTP retrieval, `feedparser` interprets RSS and Atom, `beautifulsoup4` converts summary HTML to deterministic plain text, `vaderSentiment` supplies the default lexical analyzer, and `typer` provides the CLI. The `dev` extra adds pytest, pytest-httpx, Ruff, mypy, and build tooling.

## Python API

```python
from feed_sentiment import analyze_feed, analyze_text

text_score = analyze_text("This release is excellent!")
snapshot = analyze_feed("https://example.com/feed.xml")

for item in snapshot.entries:
    print(item.entry.title, item.sentiment.label, item.sentiment.compound)

print(snapshot.snapshot_aggregate)
```

`analyze_entries(entries, *, analyzer=None)` analyzes already normalized entries. All public operations return package-owned typed dataclasses; analyzer and parser implementation objects do not leak through the API. A custom analyzer can implement the public `SentimentAnalyzer` protocol.

## CLI

```console
feed-sentiment analyze https://example.com/feed.xml
feed-sentiment analyze https://example.com/feed.xml --format json
feed-sentiment analyze http://intranet/feed.xml --allow-private-network
feed-sentiment --version
```

Normal results are written to stdout. Expected errors are concise, go to stderr, and exit 1; CLI usage errors exit 2. JSON mode emits exactly one undecorated JSON document.

## Score semantics

Each entry contains VADER `negative`, `neutral`, and `positive` proportions in `[0, 1]` plus `compound` in `[-1, 1]`. Compound scores `>= 0.05` are positive, scores `<= -0.05` are negative, and values between those thresholds are neutral. Analyzer name and installed version (when discoverable) accompany each score. Empty text is an input error rather than an artificial neutral result.

Entry analysis text is `title + "\n" + plain_text_summary` when both fields exist, or the sole usable field otherwise. HTML tags and script/style content are removed, entities decoded, whitespace collapsed, and Unicode preserved. Entries with no usable text are skipped with structured warnings.

## Snapshot aggregation

`snapshot.snapshot_aggregate` includes exactly the entries successfully analyzed in the current retrieval. Every included entry has equal weight. Negative, neutral, positive, and compound are component-wise arithmetic means calculated without intermediate rounding; the aggregate label uses the same compound thresholds. The result records included and skipped counts plus `equal_entry` weighting. If no entry succeeds, the aggregate is `None`/JSON `null`, and warnings explain empty, skipped, duplicate, or failed entries.

Within one snapshot, duplicate identity prefers entry ID, then canonical entry URL, then a SHA-256 fingerprint of normalized title, summary, and publication timestamp. This fallback is not a persistent monitoring identity contract.

## Retrieval and security boundary

Retrieval accepts only HTTP(S), uses finite connect/read timeouts, a redirect cap, a response-size limit, explicit media-type checks, and no automatic retries. The default policy rejects embedded credentials and destinations resolving to private, loopback, link-local, multicast, unspecified, or reserved addresses, including redirect targets. Trusted applications may explicitly enable private-network feeds with `RetrievalPolicy(allow_private_networks=True)`.

These checks are defense in depth for a reusable client, not a complete hosted-service SSRF sandbox. A service accepting untrusted URLs still needs network egress controls and DNS-rebinding defenses. Importing the package never performs network access.

## Known limitations

- This release analyzes one snapshot only; it has no subscriptions, persistence, `poll_once()`, history, rolling windows, or watch loop.
- VADER is lexical and English-oriented; it can miss domain context, irony, and nuanced language.
- Full article pages are not fetched. Only feed titles and summaries/content are analyzed.
- Malformed XML is rejected at document level. Recoverable missing or invalid entry metadata is represented by structured warnings.

## Development

```console
python -m pip install -e ".[dev]"
python -m pytest
python -m ruff check .
python -m mypy
python -m build
python -m twine check --strict dist/*
```

Tests use local fixtures and controlled HTTP doubles; the normal suite does not require live public feeds.

The `Quality Gates` GitHub Actions workflow runs pytest on Python 3.12, 3.13, and 3.14, then runs Ruff and mypy before validating clean wheel and source-distribution installations. CI retains seven-day diagnostic artifacts named `test-results-python-<version>`, `static-check-results`, and `package-validation-results`. Successfully validated wheel and source-distribution files are uploaded separately as `python-package-distributions` for a future publishing workflow; generated `dist/` files remain local/CI artifacts and are not committed to Git.

Production publishing setup and the maintainer release procedure are documented in [docs/releasing.md](docs/releasing.md).
