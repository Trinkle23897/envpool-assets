"""Runtime assets for EnvPool."""

from pathlib import Path

__version__ = "0.0.0"


def asset_path() -> Path:
    """Return the root directory containing EnvPool asset subtrees."""
    return Path(__file__).resolve().parent
