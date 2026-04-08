from __future__ import annotations

import sys
from pathlib import Path

from .extract_planner import build_fragment_plan


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if len(args) != 8:
        print(
            "Usage: python -m livelapse.prepare_extract_fragments "
            "<all-frames-file> <stage-dir> <date> <pad-left> <pad-right> "
            "<fragment-start> <manifest-file> <manifest-tz>",
            file=sys.stderr,
        )
        return 1

    all_frames_file = Path(args[0])
    stage_dir = Path(args[1])
    date_prefix = args[2]
    default_pad_left = int(args[3])
    default_pad_right = int(args[4])
    fragment_start = int(args[5])
    manifest_path = Path(args[6])
    manifest_tz_requested = args[7]

    try:
        plan = build_fragment_plan(
            all_frames_file=all_frames_file,
            date_prefix=date_prefix,
            default_pad_left=default_pad_left,
            default_pad_right=default_pad_right,
            fragment_start=fragment_start,
            manifest_path=manifest_path,
            manifest_tz_requested=manifest_tz_requested,
        )
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    for warning in plan.warnings:
        print(warning, file=sys.stderr)

    for fragment in plan.fragments:
        fragment_file = stage_dir / f"frag_{fragment.number_label}.txt"
        fragment_file.write_text("\n".join(fragment.selected_frames) + "\n", encoding="utf-8")

    summary_path = stage_dir / "fragments.txt"
    summary_lines = [fragment.to_summary_line() for fragment in plan.fragments]
    summary_path.write_text("\n".join(summary_lines) + "\n", encoding="utf-8")
    print(f"Prepared {len(plan.fragments)} fragment(s) from {len(plan.entries)} entries", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

