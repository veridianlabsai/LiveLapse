from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from livelapse.frame_staging import load_manifest_frame_paths, stage_frame_links, write_frame_manifest


class FrameStagingTests(unittest.TestCase):
    def test_write_frame_manifest_sorts_matching_frames(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            source_dir = tmp_path / "frames"
            source_dir.mkdir()
            (source_dir / "2026-04-06T13_09_00Z.webp").write_text("a", encoding="utf-8")
            (source_dir / "2026-04-06T13_07_00Z.webp").write_text("b", encoding="utf-8")
            (source_dir / "ignore.txt").write_text("c", encoding="utf-8")
            manifest_path = tmp_path / "frames.txt"

            count = write_frame_manifest(source_dir, "webp", manifest_path)
            manifest_lines = load_manifest_frame_paths(manifest_path)

        self.assertEqual(count, 2)
        self.assertEqual([Path(line).name for line in manifest_lines], ["2026-04-06T13_07_00Z.webp", "2026-04-06T13_09_00Z.webp"])

    def test_stage_frame_links_creates_sequential_symlinks(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            source_dir = tmp_path / "frames"
            source_dir.mkdir()
            first = source_dir / "2026-04-06T13_07_00Z.webp"
            second = source_dir / "2026-04-06T13_08_00Z.webp"
            first.write_text("a", encoding="utf-8")
            second.write_text("b", encoding="utf-8")
            stage_dir = tmp_path / "stage"

            count = stage_frame_links([str(first), str(second)], stage_dir, "webp")
            self.assertEqual(count, 2)
            self.assertTrue((stage_dir / "000001.webp").is_symlink())
            self.assertEqual((stage_dir / "000001.webp").resolve(), first.resolve())
            self.assertEqual((stage_dir / "000002.webp").resolve(), second.resolve())


if __name__ == "__main__":
    unittest.main()
