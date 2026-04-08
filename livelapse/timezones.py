from __future__ import annotations

from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

TIMEZONE_ALIASES = {
    "est": "America/New_York",
    "edt": "America/New_York",
    "et": "America/New_York",
    "eastern": "America/New_York",
    "pst": "America/Los_Angeles",
    "pdt": "America/Los_Angeles",
    "pt": "America/Los_Angeles",
    "pacific": "America/Los_Angeles",
    "cst": "America/Chicago",
    "cdt": "America/Chicago",
    "ct": "America/Chicago",
    "mst": "America/Denver",
    "mdt": "America/Denver",
    "mt": "America/Denver",
    "utc": "UTC",
    "z": "UTC",
}


def resolve_timezone(requested: str) -> str:
    cleaned = requested.strip()
    return TIMEZONE_ALIASES.get(cleaned.lower(), cleaned)


def load_zoneinfo(requested: str, *, error_label: str = "timezone") -> tuple[str, ZoneInfo]:
    resolved = resolve_timezone(requested)
    try:
        return resolved, ZoneInfo(resolved)
    except ZoneInfoNotFoundError as exc:
        raise ValueError(f"Unknown {error_label}: {requested}") from exc

