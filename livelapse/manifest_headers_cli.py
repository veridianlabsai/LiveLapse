from __future__ import annotations

import sys
from pathlib import Path

from .manifest_headers import parse_manifest_headers


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if len(args) != 1:
        print(
            "Usage: python -m livelapse.manifest_headers_cli <manifest-file>",
            file=sys.stderr,
        )
        return 1

    headers = parse_manifest_headers(Path(args[0]))
    print(f"feed={headers.feed}")
    print(f"date={headers.date}")
    print(f"manifest_tz={headers.manifest_tz}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

