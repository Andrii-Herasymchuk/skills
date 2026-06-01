"""Configuration loaded from environment variables or .env file."""

import os
from pathlib import Path


def _load_dotenv():
    """Minimal .env loader — no external dependency."""
    for candidate in [Path.cwd() / ".env", Path(__file__).resolve().parent.parent.parent / ".env"]:
        if candidate.is_file():
            with open(candidate, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    key, _, value = line.partition("=")
                    key = key.strip()
                    value = value.strip().strip("\"'")
                    if key and key not in os.environ:
                        os.environ[key] = value
            break


_load_dotenv()

BASE_URL: str = os.environ.get("SUPPA_BASE_URL", "https://modern.suppa.me").rstrip("/")
API_KEY: str = os.environ.get("SUPPA_API_KEY") or os.environ.get("SUPPA_TOKEN") or ""
LANG: str = os.environ.get("SUPPA_LANG", "en")
TZ: str = os.environ.get("SUPPA_TZ", "Europe/Kyiv")
TASKS_ENTITY_ID: int = int(os.environ.get("SUPPA_TASKS_ENTITY_ID", "37"))
