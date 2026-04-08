from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from livelapse.manifest_headers import parse_manifest_headers


class ManifestHeaderTests(unittest.TestCase):
    def test_parse_manifest_headers_reads_all_supported_keys(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest_path = Path(tmpdir) / "anomalies.txt"
            manifest_path.write_text(
                "\n".join(
                    [
                        "# feed: artemis-main",
                        "# date: 2026-04-06",
                        "# timezone: et",
                        "09:07 | ignition",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            headers = parse_manifest_headers(manifest_path)

        self.assertEqual(headers.feed, "artemis-main")
        self.assertEqual(headers.date, "2026-04-06")
        self.assertEqual(headers.manifest_tz, "et")

    def test_manifest_tz_alias_header_is_supported(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest_path = Path(tmpdir) / "anomalies.txt"
            manifest_path.write_text("# manifest-tz: utc\n", encoding="utf-8")

            headers = parse_manifest_headers(manifest_path)

        self.assertEqual(headers.manifest_tz, "utc")


if __name__ == "__main__":
    unittest.main()
