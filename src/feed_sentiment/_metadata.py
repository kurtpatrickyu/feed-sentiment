from importlib import metadata

DISTRIBUTION_NAME = "feed-sentiment"
PROJECT_URL = "https://github.com/kurtpatrickyu/feed-sentiment"
UNKNOWN_VERSION = "0+unknown"


def package_version() -> str:
    """Return the installed distribution version or a source-tree fallback."""
    try:
        return metadata.version(DISTRIBUTION_NAME)
    except metadata.PackageNotFoundError:
        return UNKNOWN_VERSION


def default_user_agent() -> str:
    """Build the default HTTP User-Agent from installed package metadata."""
    return f"{DISTRIBUTION_NAME}/{package_version()} (+{PROJECT_URL})"
