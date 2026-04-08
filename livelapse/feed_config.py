from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class FeedRecord:
    name: str
    url: str
    fps: str
    max_hours: str = ""

    def to_pipe_record(self) -> str:
        return "|".join([self.name, self.url, self.fps, self.max_hours])


def parse_feed_records(content: str) -> list[FeedRecord]:
    records: list[FeedRecord] = []

    for raw_line in content.splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        parts = [part.strip() for part in raw_line.split("|")]
        while len(parts) < 4:
            parts.append("")

        name, url, fps, max_hours = parts[:4]
        if not name or not url:
            continue

        records.append(
            FeedRecord(
                name=name,
                url=url,
                fps=fps or "1",
                max_hours=max_hours,
            )
        )

    return records


def load_feed_records(feeds_path: Path) -> list[FeedRecord]:
    return parse_feed_records(feeds_path.read_text(encoding="utf-8"))


def get_feed_record_by_name(feeds_path: Path, target: str) -> FeedRecord:
    for record in load_feed_records(feeds_path):
        if record.name == target:
            return record
    raise ValueError(f"Feed not found in feeds.conf: {target}")

