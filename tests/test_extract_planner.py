from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from zoneinfo import ZoneInfo

from livelapse.extract_planner import build_fragment_plan, parse_spec


class ExtractPlannerTests(unittest.TestCase):
    def test_parse_spec_converts_short_range_to_utc_window(self) -> None:
        zone = ZoneInfo("America/New_York")
        start, end = parse_spec("09:07-09:08", "2026-04-06", zone)

        self.assertEqual(start.isoformat(), "2026-04-06T13:07:00+00:00")
        self.assertEqual(end.isoformat(), "2026-04-06T13:08:59+00:00")

    def test_build_fragment_plan_selects_padded_frames(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            all_frames_file = tmp_path / "all_frames.txt"
            manifest_file = tmp_path / "manifest.txt"

            frame_paths = [
                "/frames/2026-04-06T13_06_00Z.webp",
                "/frames/2026-04-06T13_07_00Z.webp",
                "/frames/2026-04-06T13_08_00Z.webp",
                "/frames/2026-04-06T13_09_00Z.webp",
            ]
            all_frames_file.write_text("\n".join(frame_paths) + "\n", encoding="utf-8")
            manifest_file.write_text("09:07-09:08 | Booster sep | 1 | 1\n", encoding="utf-8")

            plan = build_fragment_plan(
                all_frames_file=all_frames_file,
                date_prefix="2026-04-06",
                default_pad_left=0,
                default_pad_right=0,
                fragment_start=1,
                manifest_path=manifest_file,
                manifest_tz_requested="et",
            )

        self.assertEqual(len(plan.entries), 1)
        self.assertEqual(len(plan.fragments), 1)
        fragment = plan.fragments[0]
        self.assertEqual(fragment.number_label, "001")
        self.assertEqual(fragment.slug, "booster-sep")
        self.assertEqual(fragment.frame_count, 4)
        self.assertEqual(fragment.selected_frames[0], "/frames/2026-04-06T13_06_00Z.webp")
        self.assertEqual(fragment.selected_frames[-1], "/frames/2026-04-06T13_09_00Z.webp")


if __name__ == "__main__":
    unittest.main()

