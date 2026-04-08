from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ManifestHeaders:
    feed: str = ""
    date: str = ""
    manifest_tz: str = ""


def _extract_header(line: str, prefixes: tuple[str, ...]) -> str:
    stripped = line.strip()
    lowered = stripped.lower()
    for prefix in prefixes:
        candidate = f"# {prefix}:"
        if lowered.startswith(candidate):
            return stripped[len(candidate) :].strip()
    return ""


def parse_manifest_headers(manifest_path: Path) -> ManifestHeaders:
    feed = ""
    date = ""
    manifest_tz = ""

    for raw_line in manifest_path.read_text(encoding="utf-8").splitlines():
        if not feed:
            feed = _extract_header(raw_line, ("feed",))
        if not date:
            date = _extract_header(raw_line, ("date",))
        if not manifest_tz:
            manifest_tz = _extract_header(raw_line, ("timezone", "manifest-tz"))

        if feed and date and manifest_tz:
            break

    return ManifestHeaders(feed=feed, date=date, manifest_tz=manifest_tz)

