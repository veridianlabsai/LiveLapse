from __future__ import annotations

from dataclasses import dataclass

from .frames import parse_frame_timestamp
from .timezones import load_zoneinfo

ASS_HEADER = """[Script Info]
ScriptType: v4.00+
WrapStyle: 0
ScaledBorderAndShadow: yes
PlayResX: 1920
PlayResY: 1080

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Timestamp,Arial,28,&H00FFFFFF,&H000000FF,&H00202020,&H00000000,0,0,0,0,100,100,0,0,1,2,0,3,24,24,24,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


@dataclass(frozen=True)
class TimestampSubtitleResult:
    resolved_timezone: str
    first_label: str
    content: str


def ass_time(seconds: float) -> str:
    total_centis = int(round(seconds * 100))
    hours, remainder = divmod(total_centis, 360000)
    minutes, remainder = divmod(remainder, 6000)
    secs, centis = divmod(remainder, 100)
    return f"{hours}:{minutes:02d}:{secs:02d}.{centis:02d}"


def ass_escape(text: str) -> str:
    return text.replace("\\", r"\\").replace("{", r"\{").replace("}", r"\}")


def build_timestamp_subtitles(
    frame_paths: list[str],
    playback_fps: float,
    requested_tz: str,
) -> TimestampSubtitleResult:
    if playback_fps <= 0:
        raise ValueError("Playback fps must be greater than 0")

    cleaned_frame_paths = [frame_path.strip() for frame_path in frame_paths if frame_path.strip()]
    if not cleaned_frame_paths:
        raise ValueError("No frames available for timestamp subtitles")

    resolved_tz, zone = load_zoneinfo(requested_tz)

    lines = [ASS_HEADER]
    first_label = ""

    for index, frame_path in enumerate(cleaned_frame_paths):
        captured_at_utc = parse_frame_timestamp(frame_path)
        captured_at_local = captured_at_utc.astimezone(zone)
        label = captured_at_local.strftime("%Y-%m-%d %H:%M:%S %Z")
        if not first_label:
            first_label = label

        start_time = ass_time(index / playback_fps)
        end_time = ass_time((index + 1) / playback_fps)
        lines.append(f"Dialogue: 0,{start_time},{end_time},Timestamp,,0,0,0,,{ass_escape(label)}\n")

    return TimestampSubtitleResult(
        resolved_timezone=resolved_tz,
        first_label=first_label,
        content="".join(lines),
    )

