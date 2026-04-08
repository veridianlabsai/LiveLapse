from __future__ import annotations

import sys
from pathlib import Path

from .frame_staging import load_manifest_frame_paths, stage_frame_links


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if len(args) != 3:
        print(
            "Usage: python -m livelapse.stage_frame_links_cli <manifest-file> <stage-dir> <frame-ext>",
            file=sys.stderr,
        )
        return 1

    manifest_path = Path(args[0])
    stage_dir = Path(args[1])
    frame_ext = args[2]

    frame_paths = load_manifest_frame_paths(manifest_path)
    print(stage_frame_links(frame_paths, stage_dir, frame_ext))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

