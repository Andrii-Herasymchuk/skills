"""Shared utilities: filters, date parsing, HTML helpers."""

import re
from datetime import datetime, timedelta, timezone


def make_filter(field: str, value, comparator: str = "=") -> dict:
    return {"field": field, "value": value, "comparator": comparator}


def normalize_filters(raw) -> list:
    """Accept a single filter dict, a list, or None → always return a list."""
    if raw is None:
        return []
    if isinstance(raw, dict):
        return [raw]
    return list(raw)


def parse_deadline(s: str) -> str:
    """Parse human-friendly deadline strings into ISO datetime."""
    now = datetime.now(timezone.utc)
    s = s.strip().lower()
    if s == "today":
        return now.replace(hour=23, minute=59, second=59).isoformat()
    if s == "tomorrow":
        return (now + timedelta(days=1)).replace(hour=23, minute=59, second=59).isoformat()
    m = re.match(r"^\+(\d+)([dhm])$", s)
    if m:
        n, unit = int(m.group(1)), m.group(2)
        delta = {"d": timedelta(days=n), "h": timedelta(hours=n), "m": timedelta(minutes=n)}[unit]
        return (now + delta).isoformat()
    # Assume ISO already
    return s


def wrap_html(text: str) -> str:
    """Wrap plain text in <p> if not already HTML."""
    if text.strip().startswith("<"):
        return text
    return f"<p>{text}</p>"


def strip_html(html: str) -> str:
    """Remove HTML tags for plain-text output."""
    return re.sub(r"<[^>]+>", "", html or "")


def json_response(data) -> str:
    """Convert data to a compact JSON string for MCP tool response."""
    import json
    return json.dumps(data, ensure_ascii=False, indent=2, default=str)
