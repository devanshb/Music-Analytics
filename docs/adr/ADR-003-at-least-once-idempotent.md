# ADR-003: At-least-once capture + idempotent load
Date: 2026-07-11 · Status: Accepted
Model context: Fable 5 architecture session; Devansh approved

## Context
Harvester can crash between fetching and recording progress. Exactly-once at
the source would require transactional coordination with Spotify (impossible).

## Decision
Write raw THEN advance watermark. Duplicates are expected and absorbed by the
plays natural key (played_at, track_id, source) with ON CONFLICT DO NOTHING;
dims upsert. Effectively-exactly-once, honestly named.

## Alternatives considered
- Advance-then-write — loses data on crash. Rejected: violates prime directive.
- Two-phase bookkeeping/outbox — machinery without a failure mode it fixes here.

## Consequences
Loader idempotency is a GATED, tested property forever (run-twice proof).
Executors must never "clean up" duplicate-tolerance as if it were a bug.
Revisit trigger: a duplicate class the natural key cannot absorb (log in Q03).
