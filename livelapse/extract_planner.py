from __future__ import annotations

import bisect
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from .frames import load_parseable_frames
from .timezones import load_zoneinfo

LINE_DATE_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})\s+(.*)")
SHORT_RANGE_RE = re.compile(r"^(\d{1,2}:\d{2}(?::\d{2})?)\s*-\s*(\d{1,2}:\d{2}(?::\d{2})?)$")
SHORT_HHMMSS_RE = re.compile(r"^\d{1,2}:\d{2}:\d{2}$")
SHORT_HHMM_RE = re.compile(r"^\d{1,2}:\d{2}$")


@dataclass(frozen=True)
class ManifestEntry:
    start: datetime
    end: datetime
    label: str
    pad_left: int
    pad_right: int


@dataclass(frozen=True)
class FragmentSelection:
    fragment_number: int
    slug: str
    selected_frames: list[str]
    label: str
    requested_start: datetime
    requested_end: datetime
    core_start: datetime
    core_end: datetime
    selected_start: datetime
    selected_end: datetime
    pad_left: int
    pad_right: int

    @property
    def frame_count(self) -> int:
        return len(self.selected_frames)

    @property
    def number_label(self) -> str:
        return f"{self.fragment_number:03d}"

    def to_summary_line(self) -> str:
        return "|".join(
            [
                self.number_label,
                self.slug,
                str(self.frame_count),
                self.label,
                self.requested_start.isoformat(),
                self.requested_end.isoformat(),
                self.core_start.isoformat(),
                self.core_end.isoformat(),
                self.selected_start.isoformat(),
                self.selected_end.isoformat(),
                str(self.pad_left),
                str(self.pad_right),
            ]
        )


@dataclass(frozen=True)
class FragmentPlan:
    entries: list[ManifestEntry]
    fragments: list[FragmentSelection]
    warnings: list[str]


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower().strip())
    return re.sub(r"-+", "-", slug).strip("-")[:60] or "fragment"


def parse_time(raw: str, date_prefix: str, manifest_zone: ZoneInfo) -> datetime:
    raw_time = raw.strip()

    if "T" in raw_time and len(raw_time) > 10:
        normalized = raw_time.replace("_", ":").rstrip("Z")
        for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M"):
            try:
                return datetime.strptime(normalized, fmt).replace(tzinfo=timezone.utc)
            except ValueError:
                continue

    if SHORT_HHMMSS_RE.match(raw_time):
        if not date_prefix:
            raise ValueError(f"--date required for short timestamp: {raw_time}")
        hours, minutes, seconds = raw_time.split(":")
        local_dt = datetime.strptime(
            f"{date_prefix}T{hours.zfill(2)}:{minutes}:{seconds}",
            "%Y-%m-%dT%H:%M:%S",
        ).replace(tzinfo=manifest_zone)
        return local_dt.astimezone(timezone.utc)

    if SHORT_HHMM_RE.match(raw_time):
        if not date_prefix:
            raise ValueError(f"--date required for short timestamp: {raw_time}")
        hours, minutes = raw_time.split(":")
        local_dt = datetime.strptime(
            f"{date_prefix}T{hours.zfill(2)}:{minutes}:00",
            "%Y-%m-%dT%H:%M:%S",
        ).replace(tzinfo=manifest_zone)
        return local_dt.astimezone(timezone.utc)

    raise ValueError(f"Cannot parse timestamp: {raw_time}")


def has_seconds(raw: str) -> bool:
    return len(raw.strip().split(":")) >= 3


def parse_spec(spec: str, date_prefix: str, manifest_zone: ZoneInfo) -> tuple[datetime, datetime]:
    cleaned = spec.strip()

    range_match = SHORT_RANGE_RE.match(cleaned)
    if range_match:
        start = parse_time(range_match.group(1), date_prefix, manifest_zone)
        end = parse_time(range_match.group(2), date_prefix, manifest_zone)
        if end < start:
            start, end = end, start
        if not has_seconds(range_match.group(2)):
            end += timedelta(seconds=59)
        return start, end

    if "," in cleaned:
        windows = []
        for raw_part in cleaned.split(","):
            part = raw_part.strip()
            parsed = parse_time(part, date_prefix, manifest_zone)
            if has_seconds(part):
                windows.append((parsed, parsed))
            else:
                windows.append((parsed, parsed + timedelta(seconds=59)))
        return min(window[0] for window in windows), max(window[1] for window in windows)

    start = parse_time(cleaned, date_prefix, manifest_zone)
    if has_seconds(cleaned):
        return start, start
    return start, start + timedelta(seconds=59)


def parse_manifest_entries(
    manifest_path: Path,
    date_prefix: str,
    default_pad_left: int,
    default_pad_right: int,
    manifest_zone: ZoneInfo,
) -> list[ManifestEntry]:
    entries: list[ManifestEntry] = []

    for raw_line in manifest_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        parts = [part.strip() for part in line.split("|")]
        timestamp_spec = parts[0]
        line_date = date_prefix

        line_date_match = LINE_DATE_RE.match(timestamp_spec)
        if line_date_match:
            line_date = line_date_match.group(1)
            timestamp_spec = line_date_match.group(2)

        label = parts[1] if len(parts) > 1 and parts[1] else timestamp_spec
        if len(parts) > 2 and parts[2]:
            pad_left = int(parts[2])
            pad_right = int(parts[3]) if len(parts) > 3 and parts[3] else pad_left
        else:
            pad_left = default_pad_left
            pad_right = default_pad_right

        start, end = parse_spec(timestamp_spec, line_date, manifest_zone)
        entries.append(
            ManifestEntry(
                start=start,
                end=end,
                label=label,
                pad_left=pad_left,
                pad_right=pad_right,
            )
        )

    if not entries:
        raise ValueError("No entries found in manifest")

    return entries


def build_fragment_plan(
    all_frames_file: Path,
    date_prefix: str,
    default_pad_left: int,
    default_pad_right: int,
    fragment_start: int,
    manifest_path: Path,
    manifest_tz_requested: str,
) -> FragmentPlan:
    _, manifest_zone = load_zoneinfo(manifest_tz_requested, error_label="manifest timezone")
    frames = load_parseable_frames(all_frames_file)
    entries = parse_manifest_entries(
        manifest_path,
        date_prefix,
        default_pad_left,
        default_pad_right,
        manifest_zone,
    )

    frame_dts = [frame[0] for frame in frames]
    fragments: list[FragmentSelection] = []
    warnings: list[str] = []

    for index, entry in enumerate(entries):
        fragment_number = fragment_start + index
        start_index = bisect.bisect_left(frame_dts, entry.start)
        end_index = bisect.bisect_right(frame_dts, entry.end)
        core_count = end_index - start_index
        if core_count == 0:
            warnings.append(
                f"Warning: no frames for fragment {fragment_number:03d} ({entry.label}): "
                f"{entry.start.isoformat()} to {entry.end.isoformat()}"
            )
            continue

        padded_start = max(0, start_index - entry.pad_left)
        padded_end = min(len(frames), end_index + entry.pad_right)
        selected_frames = [frames[position][1] for position in range(padded_start, padded_end)]

        fragments.append(
            FragmentSelection(
                fragment_number=fragment_number,
                slug=slugify(entry.label),
                selected_frames=selected_frames,
                label=entry.label,
                requested_start=entry.start,
                requested_end=entry.end,
                core_start=frames[start_index][0],
                core_end=frames[end_index - 1][0],
                selected_start=frames[padded_start][0],
                selected_end=frames[padded_end - 1][0],
                pad_left=entry.pad_left,
                pad_right=entry.pad_right,
            )
        )

    return FragmentPlan(entries=entries, fragments=fragments, warnings=warnings)

