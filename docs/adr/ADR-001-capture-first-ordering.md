# ADR-001: Capture-first ordering (harvester before warehouse)
Date: 2026-07-11 · Status: Accepted
Model context: Fable 5 architecture session; Devansh approved

## Context
recently-played is a 50-track ring buffer (~2.5–3h of listening). Data not
polled is unrecoverable. The original plan ordered OAuth → Postgres → analytics.

## Decision
Ship OAuth + harvester writing append-only raw JSONL FIRST (Days 1–2). Postgres
follows (Days 3–4). Raw files are replayable into any future schema; a schema
without data is worthless.

## Alternatives considered
- Schema-first (original plan) — cleaner pedagogy, but every pre-harvester
  heavy-listening day is permanent loss. Rejected: irrecoverable beats replayable.
- Use ListenBrainz's Spotify importer as interim capture — see ADR-008.

## Consequences
Loader must tolerate at-least-once duplicates from day one (→ ADR-003).
Harvester health becomes the project's #1 operational concern permanently.
Revisit trigger: none — this is load-bearing for the thesis.
