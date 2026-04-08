from __future__ import annotations

import sys
from pathlib import Path

from .frame_staging import write_frame_manifest


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if len(args) != 3:
        print(
            "Usage: python -m livelapse.index_frames_cli <source-dir> <frame-ext> <manifest-file>",
            file=sys.stderr,
        )
        return 1

    source_dir = Path(args[0])
    frame_ext = args[1]
    manifest_path = Path(args[2])

    print(write_frame_manifest(source_dir, frame_ext, manifest_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

