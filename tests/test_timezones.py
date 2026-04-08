from __future__ import annotations

import unittest

from livelapse.timezones import load_zoneinfo, resolve_timezone


class TimezoneTests(unittest.TestCase):
    def test_resolve_alias(self) -> None:
        self.assertEqual(resolve_timezone("et"), "America/New_York")
        self.assertEqual(resolve_timezone("UTC"), "UTC")

    def test_load_zoneinfo_raises_clear_error(self) -> None:
        with self.assertRaisesRegex(ValueError, "Unknown timezone: mars/base"):
            load_zoneinfo("mars/base")


if __name__ == "__main__":
    unittest.main()

