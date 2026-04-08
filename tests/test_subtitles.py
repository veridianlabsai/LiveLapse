from __future__ import annotations

import unittest

from livelapse.subtitles import build_timestamp_subtitles


class SubtitleTests(unittest.TestCase):
    def test_build_timestamp_subtitles_uses_resolved_timezone(self) -> None:
        result = build_timestamp_subtitles(
            [
                "/tmp/2026-04-06T14_23_07Z.webp",
                "/tmp/2026-04-06T14_23_08Z.webp",
            ],
            playback_fps=2.0,
            requested_tz="et",
        )

        self.assertEqual(result.resolved_timezone, "America/New_York")
        self.assertEqual(result.first_label, "2026-04-06 10:23:07 EDT")
        self.assertIn("Dialogue: 0,0:00:00.00,0:00:00.50", result.content)
        self.assertIn("2026-04-06 10:23:08 EDT", result.content)

    def test_build_timestamp_subtitles_rejects_empty_frame_lists(self) -> None:
        with self.assertRaisesRegex(ValueError, "No frames available for timestamp subtitles"):
            build_timestamp_subtitles([], playback_fps=1.0, requested_tz="utc")


if __name__ == "__main__":
    unittest.main()

