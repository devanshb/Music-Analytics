# INTERVIEW_DEFENSE.md — polished narratives

Purpose: the STORIES. (Raw hostile Q&A lives in QUESTION_BANK.md.) Each entry:
Situation → Decision → Tradeoff admitted → Outcome/evidence. Update after every
gate. Rule of the house: **admit the weakness before the interviewer finds it —
that is the senior move.** Entries marked [PENDING] get filled when their gate
passes; an unfilled entry after its gate is drift.

## Core narratives (required by Gate GX)

### 1. "Walk me through the system."
Longitudinal personal listening warehouse. Spotify's recently-played is a
50-track ring buffer, so capture is the irreplaceable asset: hourly harvester →
immutable raw JSONL → idempotent loads into Postgres → ISRC→MBID entity
resolution into the open MusicBrainz ecosystem → SQL metrics layer → weekly
auto-generated Wrapped. Everything downstream is replayable from raw; nothing
upstream is recoverable if missed. That asymmetry drove the build order.

### 2. Why Postgres, not SQLite?
SQLite would genuinely suffice for one user — say that first. Postgres was a
deliberate production-parity choice: ON CONFLICT upserts, timestamptz, roles
(the SELECT-only role later becomes the LLM guardrail). Knowing the simpler
tool works and choosing the heavier one with stated reasons is judgment;
pretending SQLite couldn't cope is ignorance. (ADR-002)

### 3. Delivery semantics.
At-least-once capture (write raw, then advance watermark) made effectively
exactly-once by idempotent keyed loads. True exactly-once at the source would
require transactional coordination with Spotify, which doesn't exist — so we
don't pretend. Crash-mid-run produces duplicates; the natural key absorbs them.
(ADR-003)

### 4. The API kept shrinking under you. [PENDING evidence refresh each wave]
Survived Nov 2024 (audio features, recommendations) and Feb 2026 (top-tracks,
batch, popularity, 5-user cap) during active development. Raw zone is
schema-free so captured data was never at risk; the provider seam confined
blast radius to fetchers/normalizers; API_NOTES.md re-verification per stage is
the standing defense. The March 2026 ISRC revert is the example of why we
verify rather than remember.

### 5. How do you know two plays are the same play? [PENDING D6 findings]
Export ts is second-precision stream-END; API played_at is ms-precision with
semantics we MEASURED on overlapping rows rather than trusted (findings:
API_NOTES). Dedup: same track_id within ±5s; export wins because it carries
duration/skip data. "What counts as a play" was deliberately pushed to the
metrics layer (qualified_play) so ingestion never destroys information. (ADR-005)

### 6. Entity resolution across catalogs. [PENDING G4 numbers]
Spotify track → ISRC → MusicBrainz recording. Politeness-enforced client
(1 req/s, real UA), cached resolutions, dead-letter for unresolved, NO fuzzy
fallback — coverage is an honest measured number (target ≥80% play-weighted),
not a pretended 100%. Precision over recall, and the unresolved set is
queryable with reasons.

### 7. Where does this break at 1M users?
Everywhere, on purpose: single Postgres, cron, no queue — right-sized for one
user. Scaled sketch on request: queue between fetch and load, object-storage
raw zone, orchestrator, per-user token vault, LB-style batch popularity joins.
The sketch proves the simplicity was a choice.

### 8. Worst data-quality risk?
Silent harvester death (sleeping laptop) → unrecoverable gaps. Mitigations:
heartbeats + gap-detection + the Actions migration (T0) that removes the laptop
from the loop entirely. Named before asked.

### 9. Security story.
OAuth front-channel carries only the auth code; secret + tokens back-channel
only; loopback-literal redirect per Spotify's migration; tokens chmod 600;
secrets gitignored. And the scar: an early .env leak, resolved by immediate
rotation + git rm --cached + root .gitignore — the honest version of "I take
secrets seriously" is a story, not an adjective.

## Phase 2 narratives [PENDING their gates]
10. LLM: why text-to-SQL not RAG (questions are analytical ⇒ the database IS
    the retriever; role-not-prompt guardrail; 15-question eval; a documented
    failure + fix). (T1)
11. ListenBrainz: contribute under CC0 + consume the community corpus as the
    popularity signal Spotify deleted; own harvester stays canonical (ADR-008). (T2)
12. AcousticBrainz: frozen-2022 corpus used as RELATIVE trend signal, coverage
    charted by release year, MetaBrainz's own quality caveat quoted — using
    flawed open data honestly beats pretending to clean data. (T3)
13. Public analyzer: file-processing not API-serving ⇒ Spotify limits don't
    apply; client-side-only DuckDB-WASM ⇒ zero data custody; same metric SQL
    runs in Postgres and the browser. Privacy stance as differentiator vs
    stats.fm. (T5, ADR-007)
