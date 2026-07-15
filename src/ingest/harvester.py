"""Hourly recently-played harvester -> append-only raw JSONL.

At-least-once by design (ADR-003): raw lines are written FIRST; the watermark
advances only after the write succeeds. A crash between the two produces
duplicate raw lines on the next run - the loader's natural key absorbs them.
Invariant 1: data/raw/** is append-only; this module only opens raw files in
mode "a".

Run:  .venv/bin/python -m src.ingest.harvester   (scheduled hourly via launchd)
Output: exactly one structured JSON log line on stdout per run.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

from src.common.spotify import ROOT, spotify_get

RAW_PLAYS_DIR = ROOT / "data" / "raw" / "plays"
WATERMARK_PATH = ROOT / "data" / "state" / "watermark.json"
PAGE_LIMIT = 50  # ring buffer holds 50; one call always covers it


def played_at_to_epoch_ms(played_at):
    # Spotify returns ISO-8601 UTC with ms precision, e.g. "2026-07-15T09:30:12.123Z"
    return round(datetime.fromisoformat(played_at).timestamp() * 1000)


def month_key(played_at):
    return played_at[:7]  # "YYYY-MM" - safe slice, played_at is ISO UTC


def read_watermark():
    if not WATERMARK_PATH.exists():
        return None  # first run ever: fetch without `after`
    with open(WATERMARK_PATH) as f:
        return json.load(f)["watermark_ms"]


def write_watermark(watermark_ms):
    WATERMARK_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(WATERMARK_PATH, "w") as f:
        json.dump({"watermark_ms": watermark_ms}, f)


def persist(items, fetched_at):
    """Append one envelope line per item to its month file.

    Returns (files_written, max_played_at_ms). Raising here means the
    watermark is never advanced - that ordering is the delivery guarantee.
    """
    RAW_PLAYS_DIR.mkdir(parents=True, exist_ok=True)
    by_month = {}
    for item in items:
        by_month.setdefault(month_key(item["played_at"]), []).append(item)

    files_written = []
    for month in sorted(by_month):
        path = RAW_PLAYS_DIR / f"{month}.jsonl"
        with open(path, "a", encoding="utf-8") as f:
            for item in by_month[month]:
                envelope = {"fetched_at": fetched_at, "source": "api", "payload": item}
                f.write(json.dumps(envelope, ensure_ascii=False) + "\n")
        files_written.append(str(path.relative_to(ROOT)))

    max_ms = max(played_at_to_epoch_ms(item["played_at"]) for item in items)
    return files_written, max_ms


def run():
    watermark_ms = read_watermark()
    fetched_at = datetime.now(timezone.utc).isoformat()

    params = {"limit": PAGE_LIMIT}
    if watermark_ms is not None:
        params["after"] = watermark_ms
    items = spotify_get("me/player/recently-played", params)["items"]

    if not items:
        print(json.dumps({
            "job": "harvester", "fetched_at": fetched_at, "items_fetched": 0,
            "watermark_ms": watermark_ms, "note": "no new plays",
        }))
        return

    files_written, max_ms = persist(items, fetched_at)
    new_watermark = max(watermark_ms or 0, max_ms)  # monotonic by definition
    write_watermark(new_watermark)  # ONLY after raw write succeeded (ADR-003)

    print(json.dumps({
        "job": "harvester", "fetched_at": fetched_at, "items_fetched": len(items),
        "watermark_before": watermark_ms, "watermark_after": new_watermark,
        "files": files_written,
    }))


if __name__ == "__main__":
    run()
