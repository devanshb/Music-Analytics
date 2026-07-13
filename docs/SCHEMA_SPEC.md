# SCHEMA_SPEC.md — warehouse schema (single source of truth)

schema.sql TRANSCRIBES this spec on Day 3; if they ever disagree, this file
wins and the divergence is a bug. Executors: never invent a column name — it is
either on this page or it does not exist. Changes to this file are [OPUS-PLAN]
tasks and require an ADR.

Conventions: snake_case; every timestamp is `timestamptz` stored UTC; TEXT over
VARCHAR(n); NULL means "not observed", never "false"; no ORM, raw SQL via
psycopg 3; layer prefixes in schema names later if wanted, tables below are the
core relational layer.

## Facts

### plays
| column | type | notes |
|---|---|---|
| played_at | timestamptz | UTC. API: from played_at (ms precision). Export: from ts (second precision, stream END — see API_NOTES). |
| track_id | text | Spotify track id (from URI tail for export rows) |
| source | text | 'api' \| 'export' — CHECK constraint |
| ms_played | integer NULL | export only |
| skipped | boolean NULL | export only |
| shuffle | boolean NULL | export only |
| reason_start | text NULL | export only |
| reason_end | text NULL | export only |
| platform | text NULL | export only |
| conn_country | text NULL | export only |
| ingested_at | timestamptz | default now() |
PRIMARY KEY (played_at, track_id, source). FK track_id → tracks.
Loader: INSERT ... ON CONFLICT DO NOTHING.

## Dimensions (upsert: ON CONFLICT (id) DO UPDATE — metadata can improve)

### tracks
id (text PK) · name (text) · album_id (text NULL, FK albums) · duration_ms
(integer NULL) · isrc (text NULL) · explicit (boolean NULL) · raw_first_seen_at
(timestamptz) · updated_at (timestamptz)

### albums
id (text PK) · name (text) · canonical_title (text — dedup lesson from Stage 0)
· release_year (smallint NULL — [:4] slice per API_NOTES) · release_date_raw
(text NULL) · updated_at (timestamptz)

### artists
id (text PK) · name (text) · mbid (uuid NULL — filled by enrichment) · country
(text NULL) · artist_type (text NULL) · begin_year (smallint NULL) · updated_at
(timestamptz)

### track_artists  (tracks↔artists is MANY-TO-MANY — invariant 7)
track_id (text FK) · artist_id (text FK) · position (smallint) ·
PRIMARY KEY (track_id, artist_id)

## Enrichment

### mb_resolution
isrc (text PK) · mbid (uuid NULL) · status (text CHECK: resolved | unresolved |
error) · fetched_at (timestamptz) · payload (jsonb)

### track_genres
track_id (text FK) · genre (text) · source (text, e.g. 'mb') · score (real NULL)
· PRIMARY KEY (track_id, genre, source)

### catalog_missing
track_id (text PK) · export_track_name (text) · export_artist_name (text) ·
first_seen_at (timestamptz) · last_error (text)

## Operational

### ingest_ledger
file_path (text PK) · processed_at (timestamptz) · rows_seen (integer) ·
rows_inserted (integer) · rows_conflicted (integer)
(Transaction boundary = one raw file: rows + ledger row commit together.)

### heartbeat
id (bigserial PK) · job (text: harvester | loader | enrich_mb | report | ...) ·
started_at (timestamptz) · finished_at (timestamptz NULL) · status (text CHECK:
ok | error) · note (text NULL)

## Phase 2 additions (spec'd when their track starts — placeholders, not built in sprint)
- lb_submission_ledger; lb_popularity_artist / lb_popularity_recording (T2)
- ab_features (recording_mbid PK, high-level jsonb, selected columns, frozen_at note) (T3)
- events_cache + artist_event_mismatch (T4)
- Postgres role `llm_readonly`: SELECT on marts views only, statement_timeout set (T1)

## Marts
Views/materialized views defined per docs/METRIC_DEFINITIONS.md, prefixed
`mv_`/`v_`. The LLM role sees ONLY these.
