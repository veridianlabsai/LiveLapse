from __future__ import annotations

import sys
from pathlib import Path

from .feed_config import get_feed_record_by_name, load_feed_records


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if len(args) < 2:
        print(
            "Usage: python -m livelapse.feed_config_cli "
            "<list-records|record-by-name|list-names> <feeds.conf> [feed-name]",
            file=sys.stderr,
        )
        return 1

    command = args[0]
    feeds_path = Path(args[1])

    try:
        if command == "list-records":
            for record in load_feed_records(feeds_path):
                print(record.to_pipe_record())
            return 0

        if command == "record-by-name":
            if len(args) != 3:
                print("record-by-name requires a feed name", file=sys.stderr)
                return 1
            print(get_feed_record_by_name(feeds_path, args[2]).to_pipe_record())
            return 0

        if command == "list-names":
            for record in load_feed_records(feeds_path):
                print(record.name)
            return 0
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(f"Unknown feed-config command: {command}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

