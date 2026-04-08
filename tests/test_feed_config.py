from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from livelapse.feed_config import get_feed_record_by_name, parse_feed_records


class FeedConfigTests(unittest.TestCase):
    def test_parse_feed_records_trims_and_defaults_fps(self) -> None:
        records = parse_feed_records(
            """
            # comment
            artemis-main | https://example.com/live | 0.2 | 48
            construction-cam|rtsp://cam.local/stream||
            missing-url||
            """
        )

        self.assertEqual(len(records), 2)
        self.assertEqual(records[0].to_pipe_record(), "artemis-main|https://example.com/live|0.2|48")
        self.assertEqual(records[1].to_pipe_record(), "construction-cam|rtsp://cam.local/stream|1|")

    def test_get_feed_record_by_name_reads_from_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            feeds_path = Path(tmpdir) / "feeds.conf"
            feeds_path.write_text("alpha|https://example.com/live|1|24\n", encoding="utf-8")

            record = get_feed_record_by_name(feeds_path, "alpha")

        self.assertEqual(record.name, "alpha")
        self.assertEqual(record.max_hours, "24")


if __name__ == "__main__":
    unittest.main()

