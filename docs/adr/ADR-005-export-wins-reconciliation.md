# ADR-005: Export-wins reconciliation (±5s window)
Date: 2026-07-11 · Status: Proposed — finalize with D6 measurements
Model context: Fable 5 design; OPUS-PLAN to confirm with data on D6

## Context
GDPR export (ts = second-precision stream END) and API (played_at =
ms-precision, semantics to be MEASURED not assumed) overlap for the
harvester-live period and describe the same plays differently.

## Decision (proposed)
Same play ⇔ same track_id AND |Δt| ≤ 5s across sources. On duplication the
export row wins (carries ms_played/skipped/shuffle/reasons). Podcasts/
audiobooks excluded from v1 ingestion. "What counts as a play" is deferred to
the metrics layer (qualified_play), never decided at ingestion.

## Alternatives considered
- API-wins — discards duration/skip data. Rejected.
- Keep both flagged — doubles counts in every metric or pushes dedup into
  every query. Rejected: one canonical row, provenance in `source`.
- Exact-timestamp match — fails on known precision mismatch. Rejected.

## Consequences
A one-time reconciliation pass + a standing invariant on export imports.
FINALIZATION REQUIREMENT: paste measured Δt distribution + window sensitivity
into this ADR on D6 and flip to Accepted. Revisit trigger: overlap disagreement
rate above ~1% (then re-measure semantics).
