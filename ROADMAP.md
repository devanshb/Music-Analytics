# ROADMAP — Music-Analytics: Personal Listening Data Warehouse

**Thesis:** The differentiator is longitudinal personal listening data that cannot be
obtained retroactively, processed with real data-engineering discipline, enriched
from open CC0 sources (MusicBrainz / ListenBrainz / AcousticBrainz), and served
through a weekly auto-generated report plus (Phase 2) an LLM layer and a
privacy-first public analyzer.

**Prime directive:** recently-played is a 50-track ring buffer. Uncaptured
listening is lost forever. Ingestion continuity outranks every feature.

**Structure:** Phase 1 = 14-day sprint → interview-defensible system (v0.1.0).
Phase 2 = 2–3+ months of standout tracks. Every task carries a model tag
(see docs/MODEL_ROUTING.md). Every gate is a literal checklist; a gate is passed
only when its evidence is logged in PROGRESS.md. **Gates may slip. Gates may
never be skipped.**

Decisions live in docs/adr/. Verified API facts live in API_NOTES.md.
Schema truth lives in docs/SCHEMA_SPEC.md (later mirrored by schema.sql).

---

# PHASE 1 — THE 14-DAY SPRINT (v0.1.0: interview-defensible)

Scope: OAuth + harvester → warehouse → GDPR backfill + reconciliation →
MusicBrainz enrichment → metrics layer → Weekly Wrapped + reliability.
Explicitly OUT of sprint scope: LLM features, ListenBrainz, AcousticBrainz,
concert radar, public analyzer, era clustering. They are Phase 2. Any executor
proposing them during the sprint is drifting — stop and re-read this line.

**Day 0 (before the sprint, TODAY):** request "Extended streaming history" from
the Spotify privacy page. Multi-day lead time; it must be in flight before Day 1.

### Daily rhythm (every sprint day)
1. Morning [OPUS-PLAN]: read PROGRESS.md + today's block; produce a written plan
   (files touched, invariants affected); Devansh approves.
2. Execution [SONNET-EXEC]: implement against the approved plan. /clear between
   unrelated tasks.
3. Evening [SONNET]: run the day's verification commands; append evidence to
   PROGRESS.md; add ≥1 question to docs/QUESTION_BANK.md if a decision was made;
   write/update ADR if a decision was made; commit.

---

## Days 1–2 — OAuth2 + Live Harvester
Tag: [OPUS-PLAN → SONNET-EXEC]

**D1: OAuth Authorization Code flow**
- Scope `user-read-recently-played`; redirect `http://127.0.0.1:<fixed-port>/callback`
  (loopback IP literal, never `localhost`).
- Random `state`, verified on callback (throw on mismatch).
- Token persistence: `secrets/tokens.json`, mode 600, store issued_at + expires_in;
  compute expiry locally. Refresh on expiry; refresh failure → THROW with
  "re-run auth" message. No retry loops around auth.

**D2: Harvester + scheduling**
- Watermark = max played_at (epoch ms) successfully written; state file for now.
- Run: read watermark → GET recently-played (limit=50, after=watermark) via the
  existing `spotify_get` gateway → empty items ⇒ log + exit 0 → append each item
  as one line to `data/raw/plays/YYYY-MM.jsonl` in envelope
  `{fetched_at, source:"api", payload:{...}}` → advance watermark ONLY after
  write succeeds (at-least-once by design) → one structured log line.
- Schedule hourly via macOS launchd (50 tracks ≈ 2.5–3 h listening ⇒ 3× margin).
  GitHub Actions migration is Phase 2 (T0) — do not build it now.

**GATE G1 — checklist (evidence → PROGRESS.md)**
- [ ] Auth flow completes end-to-end; tokens file exists with mode 600
- [ ] `git status` clean of secrets; `secrets/` and `.env` gitignored
- [ ] Two consecutive manual harvester runs: second run fetches only new plays
      (watermark proof — paste both log lines)
- [ ] launchd job installed; one unattended run observed in logs
- [ ] Kill harvester mid-run, rerun: no data loss, duplicates tolerated (paste proof)
- [ ] GDPR export request confirmed in flight (Day 0 done)

---

## Days 3–4 — Postgres Warehouse
Tag: [OPUS-PLAN → SONNET-EXEC] (schema day is Opus-planned, no exceptions)

**D3: Schema + first loader**
- Postgres 16 via Docker compose (one service, pinned image). Write schema.sql
  from docs/SCHEMA_SPEC.md — the spec is the source of truth; the DDL transcribes it.
- Tables: plays (fact), tracks, albums, artists, track_artists (bridge — tracks
  have MULTIPLE artists), ingest_ledger, heartbeat.
- Loader: consult ingest_ledger for unprocessed raw files → normalize → upsert
  dims (`ON CONFLICT DO UPDATE`) → insert facts (`ON CONFLICT DO NOTHING` on
  (played_at, track_id, source)) → mark file processed IN THE SAME TRANSACTION.
  Malformed line ⇒ THROW (never skip).

**D4: Hardening + DQ v1**
- Post-load checks that THROW: duplicate natural keys, NULL track_id, non-UTC
  timestamps, daily row count anomaly (>5σ from trailing mean once history exists).
- Heartbeat: harvester + loader write a row per run (job, started_at, status, note).

**GATE G2**
- [ ] `load` run twice back-to-back ⇒ identical row counts (paste both counts)
- [ ] Row count in plays == manual line count from raw files minus documented dupes
- [ ] All timestamps timestamptz UTC (paste a `SELECT ... AT TIME ZONE` proof)
- [ ] Malformed-line fixture makes loader THROW (paste the traceback)
- [ ] schema.sql matches SCHEMA_SPEC.md exactly (column-by-column diff done)

---

## Days 5–7 — GDPR Backfill + Reconciliation (D7 = buffer/consolidation)
Tag: [OPUS-PLAN → SONNET-EXEC]; reconciliation design itself is [OPUS]

**D5: Import**
- Parse Streaming_History_Audio_*.json; keep music rows (spotify_track_uri
  non-null); podcasts/audiobooks out of scope v1 (note in ADR-005).
- Insert source='export' with ms_played, skipped, shuffle, reason_start/end,
  platform, conn_country. API rows leave these NULL (NULL = not observed).
- Missing track dims → resumable single-track GET job (ledger + checkpoint;
  batch endpoints are gone). Catalog 404s → `catalog_missing` table with the
  export's name/artist strings (bookkeeping, not fallback).

**D6: Reconciliation**
- Empirically measure API `played_at` vs export `ts` semantics on overlapping
  rows BEFORE coding the dedup. Document the finding in API_NOTES.md.
- Dedup rule v1: same play ⇔ same track_id AND |Δt| ≤ 5s. Export wins (richer).
- "What counts as a play" is a METRICS decision (qualified_play), not ingestion.
  Raw keeps everything, including 2-second skips.

**D7: Buffer** — finish spillover; write ADR-005 with measured findings; harvester
health check (it has now run unattended ~5 days — inspect gaps).

**GATE G3**
- [ ] Lifetime play count == export line count − documented exclusions (numbers pasted)
- [ ] "Plays per year" query returns a continuous series, no cliff at harvester start
- [ ] Overlap-window study written into API_NOTES.md with measured Δt distribution
- [ ] Re-running the export import is a no-op (paste counts)
- [ ] ADR-005 committed with status Accepted + findings

---

## Days 8–9 — MusicBrainz Enrichment (entity resolution)
Tag: [SONNET-EXEC against the already-specified design; escalate on surprises]

- Precondition (D8 morning): verify `external_ids.isrc` still present on the
  track endpoint (volatile: removed Feb 2026, reverted Mar 2026). Log in API_NOTES.
- Client: hard 1 req/s, User-Agent `MusicAnalytics/1.0 (email)`, every lookup
  cached in mb_resolution(isrc, mbid, status, fetched_at, payload). Resumable.
- ISRC → recording MBID → recording+artist with genre/tag includes →
  track_genres(track_id, genre, source='mb', score) + artist country/type/begin.
- No fuzzy fallback. Unresolved = status row + NULL genre. Coverage is a metric.
- Overnight batch between D8→D9 (≈1s per unique track).

**GATE G4**
- [ ] ≥80% of plays (play-weighted) have ≥1 genre — paste the coverage query result
- [ ] Kill-and-resume proof on the batch job (paste before/after cache counts)
- [ ] Zero requests above 1 req/s (paste client throttle test)
- [ ] Unresolved tracks queryable with reasons

---

## Days 10–11 — Metrics Layer
Tag: [OPUS-PLAN for definitions → SONNET-EXEC for SQL + fixtures]

Definitions FIRST (docs/METRIC_DEFINITIONS.md — this doc later grounds the LLM):
1. Sessions (gap > 30 min via LAG) 2. Discovery rate (weekly % first-ever plays)
3. Genre entropy per month (Shannon) 4. Taste drift (1 − cosine of adjacent
months' artist vectors) 5. Skip behavior (export rows only) 6. Resurrections
(return after ≥180 dormant days) + nostalgia index 7. Listening clock + platform
history. Every metric: written definition ≤2 sentences a non-engineer gets,
a view, and one fixture test with hand-computed expected output.

**GATE G5**
- [ ] METRIC_DEFINITIONS.md complete; every metric has definition + view + passing fixture
- [ ] qualified_play defined in writing and used consistently
- [ ] Taste-drift chart eyeballed against known life events (sanity narrative in PROGRESS)

---

## Days 12–13 — Weekly Wrapped + Reliability
Tag: [SONNET-EXEC]

- D12: report generator — marts queries → ONE templating approach → ONE chart
  method (pick and record) → static `reports/YYYY-WW.html`. Render first real report.
- D13: gap-detection query (no successful harvest >6h ⇒ flag; hour-gaps in plays
  cross-checked against heartbeats); wire DQ suite post-load; scheduler entry for
  Monday report; README pass.

**GATE G6**
- [ ] A real Wrapped HTML exists from live warehouse data (path in PROGRESS)
- [ ] Gap detection catches a synthetic gap (paste test)
- [ ] System survives laptop reboot with zero manual repair (performed + logged)

---

## Day 14 — Interview-Defense Day + Phase-1 Exit
Tag: [OPUS] for defense-doc review; [FABLE-REVIEW] if a monthly slot is available

- Update docs/QUESTION_BANK.md: every open question gets a drafted honest answer.
- Update docs/INTERVIEW_DEFENSE.md narratives (see doc for required entries).
- Full PROGRESS.md gate audit; tag v0.1.0.

**GATE GX — Phase 1 exit**
- [ ] Gates G1–G6 all evidenced in PROGRESS.md
- [ ] Harvester unattended streak ≥ 10 days with gaps explained
- [ ] A stranger can clone + read README and understand the system in 10 minutes
      (test on a fresh Claude session with ONLY README in context)
- [ ] QUESTION_BANK has ≥25 answered questions; INTERVIEW_DEFENSE has all core narratives
- [ ] v0.1.0 tagged

---

# PHASE 2 — ELEVATION TRACKS (2–3+ months)

Rules: one track in flight at a time. Every track: Opus plans, Sonnet executes,
gate evidenced in PROGRESS.md, ADR for every decision, ≥3 new QUESTION_BANK
entries. The API admission rule (ADR-004) governs every integration:
joins on an existing warehouse entity AND powers a metric/report feature, or it
does not enter. Order below is recommended; T0 first, then T1; reorder the rest
deliberately (write why in PROGRESS).

## T0 — Always-on harvester (GitHub Actions)  [OPUS-PLAN → SONNET-EXEC]
Private repo; scheduled workflow (cron) runs the plain-Python harvester; client
secret + refresh token in Actions secrets; watermark + raw JSONL committed back
by the workflow. NOTE: this workflow runs Python, never `claude -p` — headless
Claude usage bills to a separate credit pool (see MODEL_ROUTING).
**Gate T0:** 7 consecutive cloud runs green; laptop fully off during ≥1 heavy
listening day with zero loss; secrets scan of repo history clean.

## T1 — LLM Intelligence Layer  [OPUS designs prompts+guardrails; SONNET wires]
Iron rule: the LLM never computes numbers. SQL computes; the LLM narrates/translates.
- Wrapped narration: metrics payload + METRIC_DEFINITIONS → one LLM call → HTML
  insert; digit-tripwire (any number in output not present in payload ⇒ flag).
- NL Q&A (text-to-SQL): context = schema.sql + METRIC_DEFINITIONS; execution
  ONLY through a SELECT-only Postgres role granted on marts views with
  statement_timeout. The guardrail is the role, not the prompt.
- Eval set: 15 hand-verified questions; re-run after any prompt/schema change.
**Gate T1:** narration live with tripwire passing; ≥12/15 eval; one documented
failure case + fix; ADR on model/provider choice for the feature.

## T2 — ListenBrainz (two directions)  [OPUS-PLAN → SONNET-EXEC]
2a Submit: batch submitter reads warehouse (NOT the harvester — harvester stays
sacred), maps to LB listen payloads (recording metadata + spotify_id/isrc in
additional_info), respects LB's "half the track or 4 min" qualified-listen rule
using export ms_played where available; token auth; idempotent via submission
ledger. Optionally import the GDPR export via LB's own importer — decide, ADR it.
2b Consume: popularity endpoints (artist/recording listen+listener counts by MBID,
batched) + sitewide tops + similar-artists → lb_popularity cache tables →
new metric family: mainstreamness score over time, contrarian index,
"discovered before the crowd" flags. Politeness: respect LB rate headers.
**Gate T2:** own LB profile shows lifetime history; mainstreamness metric in
Wrapped with fixture; ADR-008 finalized (own harvester canonical — why).

## T3 — AcousticBrainz Audio Features  [SONNET-EXEC; OPUS if API is down]
Precondition: one curl to the AB API. Up ⇒ batch fetch high-level (+selected
low-level) by recording MBID, ≤25/request, honor X-RateLimit headers, cache table,
resumable. Down ⇒ fall back to the frozen dump (high-level archive; targeted
extraction for owned MBIDs only) — that switch is an ADR, not a fallback branch.
Features stored with source + frozen-at note. Metrics: energy/valence-proxy/BPM
trends across eras; coverage-by-release-year chart REQUIRED in the report
(the 2022 freeze is shown, not hidden). Data used as relative trend signal only —
MetaBrainz's own quality caveat is quoted in INTERVIEW_DEFENSE.
Stretch T3b [OPUS-PLAN first]: local analysis (librosa or Essentia) on 30s
previews for post-2022 gap-fill. Preview source (Deezer/iTunes) availability and
ToS = verify-at-build; macOS install feasibility = verify-at-build. May be
rejected; rejection is a valid ADR outcome.
**Gate T3:** feature coverage measured + charted; ≥2 audio-trend metrics with
fixtures; honest-limitations paragraph in INTERVIEW_DEFENSE.

## T4 — Concert Radar (small)  [SONNET-EXEC]
Top-N artists trailing 90d × ONE events API (Bandsintown or Ticketmaster —
choose, ADR why) × home radius → weekly-cached → Wrapped section. Name-based
matching risk logged in a mismatch table (same pattern as mb_resolution).
**Gate T4:** section renders; cache proven (zero API calls on re-render).

## T5 — Public Analyzer (client-side only)  [OPUS-heavy design → SONNET-EXEC]
Static site; visitor drops their my_spotify_data.zip; ALL parsing + SQL run
in-browser (Web Worker + DuckDB-WASM). The metric SQL is shared with the
warehouse — write once, run in Postgres and in the browser. HARD INVARIANT
(ADR-007): no upload endpoint, no server-side processing, no analytics that
exfiltrate listen data. The privacy stance is the product.
**Gate T5:** a friend's export analyzed locally with network tab proving zero
data egress (screenshot in PROGRESS); shared-SQL proof (same file, two engines,
same numbers on a fixture); README section + screenshots.

## T6 — Era Clustering + Write-ups  [OPUS for the analysis; SONNET for plumbing]
K-means over monthly genre/audio vectors → named "musical eras" annotated in
Wrapped (pairs with T1 narration). Two blog posts, each on ONE hard problem
(timestamp reconciliation; ISRC entity resolution; text-to-SQL guardrails;
client-side analytics). A good post outperforms three features.
**Gate T6:** eras render with human-reviewed names; ≥1 post published.

---

## Standing interview-defense protocol
After every gate: ≥3 new questions with honest answers → QUESTION_BANK.md;
narratives updated in INTERVIEW_DEFENSE.md; decisions ADR'd. Day-14 and every
monthly [FABLE-REVIEW] audit this trail (protocol: docs/FABLE_REVIEW.md).
