"""Build-wheel smoke test; run from the repository root after ``python -m build``."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


def run(
    *args: str, cwd: Path, env: dict[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(args, cwd=cwd, env=env, text=True, capture_output=True)
    if result.returncode:
        raise RuntimeError(
            f"Command failed ({result.returncode}): {' '.join(args)}\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
    return result


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    wheels = list((root / "dist").glob("feed_sentiment-*.whl"))
    if len(wheels) != 1:
        raise SystemExit("Expected exactly one built feed-sentiment wheel")
    with tempfile.TemporaryDirectory(prefix="feed-sentiment-smoke-") as raw_temp:
        temp = Path(raw_temp)
        environment = temp / "venv"
        run(sys.executable, "-m", "venv", str(environment), cwd=temp)
        python = environment / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        command = environment / (
            "Scripts/feed-sentiment.exe" if os.name == "nt" else "bin/feed-sentiment"
        )
        run(str(python), "-m", "pip", "install", str(wheels[0]), cwd=temp)
        result = run(
            str(python),
            "-c",
            "import json, feed_sentiment; "
            "from feed_sentiment import RetrievalPolicy; "
            "print(json.dumps({'label': feed_sentiment.analyze_text('excellent').label, "
            "'version': feed_sentiment.__version__, "
            "'user_agent': RetrievalPolicy().user_agent}))",
            cwd=temp,
        )
        installed = json.loads(result.stdout)
        assert installed["label"] == "positive"
        assert installed["user_agent"] == (
            f"feed-sentiment/{installed['version']} "
            "(+https://github.com/kurtpatrickyu/feed-sentiment)"
        )
        run(str(command), "--help", cwd=temp)
        assert run(str(command), "--version", cwd=temp).stdout.strip() == "0.1.0"

        fixture_dir = root / "tests" / "fixtures"

        handler = partial(SimpleHTTPRequestHandler, directory=str(fixture_dir))
        server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            url = f"http://127.0.0.1:{server.server_port}/rss.xml"
            snapshot = json.loads(
                run(
                    str(command),
                    "analyze",
                    url,
                    "--allow-private-network",
                    "--format",
                    "json",
                    cwd=temp,
                ).stdout
            )
            assert len(snapshot["entries"]) == 2
        finally:
            server.shutdown()


if __name__ == "__main__":
    main()
