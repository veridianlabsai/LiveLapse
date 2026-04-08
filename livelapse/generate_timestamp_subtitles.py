from __future__ import annotations

import sys
from pathlib import Path

from .subtitles import build_timestamp_subtitles


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if len(args) != 4:
        print(
            "Usage: python -m livelapse.generate_timestamp_subtitles "
            "<manifest-file> <subtitles-file> <playback-fps> <timezone>",
            file=sys.stderr,
        )
        return 1

    manifest_path = Path(args[0])
    subtitles_path = Path(args[1])
    playback_fps = float(args[2])
    requested_tz = args[3]

    frame_paths = [line.strip() for line in manifest_path.read_text(encoding="utf-8").splitlines() if line.strip()]

    try:
        result = build_timestamp_subtitles(frame_paths, playback_fps, requested_tz)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    subtitles_path.write_text(result.content, encoding="utf-8")
    print(f"{result.resolved_timezone}|{result.first_label}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

