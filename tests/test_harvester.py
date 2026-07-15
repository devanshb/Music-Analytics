"""Harvester unit tests - no network; spotify_get is mocked.

Covers the G1-relevant properties: watermark advances only after a successful
raw write, second run passes `after`, empty response is a clean no-op, and a
crash-refetch produces duplicate raw lines (at-least-once, ADR-003) rather
than data loss.
"""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.ingest import harvester


def item(played_at, track_id="t1"):
    return {"played_at": played_at, "track": {"id": track_id, "name": "song"}, "context": None}


class PureHelpers(unittest.TestCase):
    def test_epoch_ms_at_epoch(self):
        self.assertEqual(harvester.played_at_to_epoch_ms("1970-01-01T00:00:01.5Z"), 1500)

    def test_epoch_ms_known_instant(self):
        # 2020-01-01T00:00:00Z is 1577836800 s since epoch (hand-computed)
        self.assertEqual(harvester.played_at_to_epoch_ms("2020-01-01T00:00:00Z"), 1577836800000)
        self.assertEqual(harvester.played_at_to_epoch_ms("2020-01-01T00:00:00.123Z"), 1577836800123)

    def test_month_key(self):
        self.assertEqual(harvester.month_key("2026-07-15T09:30:12.123Z"), "2026-07")


class WithTempWarehouse(unittest.TestCase):
    """Points the module's paths into a temp dir for the duration of each test."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: __import__("shutil").rmtree(self.tmp))
        self.enterContext(patch.multiple(
            harvester,
            ROOT=self.tmp,
            RAW_PLAYS_DIR=self.tmp / "data" / "raw" / "plays",
            WATERMARK_PATH=self.tmp / "data" / "state" / "watermark.json",
        ))

    def raw_lines(self, month):
        path = self.tmp / "data" / "raw" / "plays" / f"{month}.jsonl"
        with open(path) as f:
            return [json.loads(line) for line in f]


class PersistTests(WithTempWarehouse):
    def test_envelope_shape_and_month_split(self):
        items = [
            item("2026-06-30T23:59:59.5Z", "a"),
            item("2026-07-01T00:00:00Z", "b"),
            item("2026-07-02T10:00:00Z", "c"),
        ]
        files, max_ms = harvester.persist(items, "2026-07-15T00:00:00+00:00")

        self.assertEqual(files, ["data/raw/plays/2026-06.jsonl", "data/raw/plays/2026-07.jsonl"])
        self.assertEqual(max_ms, harvester.played_at_to_epoch_ms("2026-07-02T10:00:00Z"))

        june, july = self.raw_lines("2026-06"), self.raw_lines("2026-07")
        self.assertEqual(len(june), 1)
        self.assertEqual(len(july), 2)
        envelope = june[0]
        self.assertEqual(envelope["source"], "api")
        self.assertEqual(envelope["fetched_at"], "2026-07-15T00:00:00+00:00")
        self.assertEqual(envelope["payload"]["track"]["id"], "a")


class RunTests(WithTempWarehouse):
    def test_first_run_no_after_param_and_watermark_written(self):
        items = [item("2026-07-14T10:00:00Z"), item("2026-07-14T11:00:00Z")]
        with patch.object(harvester, "spotify_get", return_value={"items": items}) as mock_get:
            harvester.run()
        self.assertEqual(mock_get.call_args[0][1], {"limit": 50})  # no `after` on first run
        self.assertEqual(
            harvester.read_watermark(),
            harvester.played_at_to_epoch_ms("2026-07-14T11:00:00Z"),
        )

    def test_second_run_passes_after_and_empty_is_noop(self):
        harvester.write_watermark(1234567890123)
        with patch.object(harvester, "spotify_get", return_value={"items": []}) as mock_get:
            harvester.run()
        self.assertEqual(mock_get.call_args[0][1], {"limit": 50, "after": 1234567890123})
        self.assertEqual(harvester.read_watermark(), 1234567890123)  # unchanged
        self.assertFalse((self.tmp / "data" / "raw" / "plays").exists())  # nothing written

    def test_crash_refetch_duplicates_absorbed_not_lost(self):
        # Simulate: run succeeds, crash before watermark advance is emulated by
        # resetting the watermark, then the same window is refetched.
        items = [item("2026-07-14T10:00:00Z")]
        with patch.object(harvester, "spotify_get", return_value={"items": items}):
            harvester.run()
            harvester.WATERMARK_PATH.unlink()  # "crash" erased the advance
            harvester.run()
        lines = self.raw_lines("2026-07")
        self.assertEqual(len(lines), 2)  # duplicate lines present - by design
        self.assertEqual(lines[0]["payload"], lines[1]["payload"])  # no loss, no corruption

    def test_watermark_not_advanced_when_persist_fails(self):
        items = [item("2026-07-14T10:00:00Z")]
        with patch.object(harvester, "spotify_get", return_value={"items": items}), \
             patch.object(harvester, "persist", side_effect=OSError("disk full")):
            with self.assertRaises(OSError):
                harvester.run()
        self.assertIsNone(harvester.read_watermark())  # never advanced past unwritten data


if __name__ == "__main__":
    unittest.main()
