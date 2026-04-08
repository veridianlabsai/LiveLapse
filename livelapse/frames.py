from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

FRAME_TIMESTAMP_FORMAT = "%Y-%m-%dT%H_%M_%SZ"


def parse_frame_timestamp(frame_path: str) -> datetime:
    stem = Path(frame_path).stem
    try:
        return datetime.strptime(stem, FRAME_TIMESTAMP_FORMAT).replace(tzinfo=timezone.utc)
    except ValueError as exc:
        raise ValueError(f"Could not parse frame timestamp from {frame_path}") from exc


def load_parseable_frames(index_path: Path) -> list[tuple[datetime, str]]:
    frames: list[tuple[datetime, str]] = []

    for raw_line in index_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        stem = Path(line).stem
        try:
            captured_at = datetime.strptime(stem, FRAME_TIMESTAMP_FORMAT).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
        frames.append((captured_at, line))

    if not frames:
        raise ValueError("No parseable frames found")

    return frames

