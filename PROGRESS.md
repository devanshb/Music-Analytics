# PROGRESS.md — gate evidence log

Rules: a gate is PASSED only when its checklist appears here with pasted
evidence (commands + output snippets) and a date. No evidence ⇒ not passed.
Executors append; never rewrite history. Slipped gates get a dated SLIP note
with reason — slipping is honest, skipping is drift.

Template per entry:
## <date> — <gate or milestone>
Model used: [OPUS-PLAN/SONNET-EXEC/...]
Checklist:
- [x] item — evidence: `command` → output
Decisions made today (→ ADR refs):
New QUESTION_BANK entries: Qnn–Qmm
Handoff note (state / verified / next):

---
## 2026-07-11 — Repo scaffolded (pre-Day-0)
Scaffold generated (Fable 5 architecture session). Next actions:
1. Day 0: request Extended streaming history from Spotify privacy page — TODAY.
2. Copy .env.example → .env, fill Spotify creds; create secrets/; confirm gitignore.
3. Begin Day 1 per ROADMAP with an [OPUS-PLAN] morning block.

---
## 2026-07-12 — Pre-Day-1 review (docs + structure)
Model used: [FABLE — review session]
Findings:
- All docs cross-checked (README, ROADMAP, CLAUDE.md, API_NOTES, SCHEMA_SPEC,
  METRIC_DEFINITIONS, DATA_SOURCES, MODEL_ROUTING, SKILLS, FABLE_REVIEW,
  INTERVIEW_DEFENSE, QUESTION_BANK, 8 ADRs + index): internally consistent —
  plays natural key, qualified_play semantics, gate structure, and ADR statuses
  all agree across files.
- FIXED: .gitignore covered only `.venv`/`.env` — invariant 13 requires
  `secrets/` ignored, and tokens.json lands there on Day 1. Added `secrets/*`
  (keeping .gitkeep), `data/raw/plays/`, `data/export/`, `__pycache__/`,
  `.DS_Store`.
- GitHub remote is PUBLIC (unauthenticated `api.github.com/repos/...` → 200).
  Harvester plays + GDPR export must never be committed here; ignore rules
  added as the safe default. DECISION PENDING: make repo private vs keep
  personal data untracked (T0 already assumes a private repo).
- Skills referenced by CLAUDE.md/SKILLS.md (.claude/skills/*) do not exist yet.
  Recommendation: write each skill when its domain gets built (spotify-api
  after D1–2, warehouse-sql after D3–4, ...), not speculatively.
- Entire 2026-07-11 scaffold is UNCOMMITTED (docs/, src/, ROADMAP, etc.) plus
  Stage-0 leftovers (modified CSVs, 7 album_tracks JSONs). Needs a scaffold
  commit before Day 1 work.
- Day 0 (GDPR export request) still unconfirmed — G1 checklist item.
- API_NOTES extended: OAuth code-flow + refresh mechanics verified against
  official docs 2026-07-12 (Basic-header auth; refresh_token may be omitted on
  refresh; ~6-month refresh-token lifetime).
Handoff (state / verified / next): .gitignore + API_NOTES + this entry are the
only changes; nothing else touched. Next: commit scaffold, confirm Day 0,
approve D1 plan, build auth module.

---
## 2026-07-15 — Days 1–2 implementation (auth + harvester), G1 partially evidenced
Model used: [FABLE — Devansh set /model explicitly; D1–2 is tagged OPUS-PLAN→SONNET-EXEC]
Built:
- src/common/spotify.py — OAuth Authorization Code (loopback 127.0.0.1:8888,
  random state verified, throws on mismatch/denial), tokens →
  secrets/tokens.json created 0o600 via os.open, expiry computed locally,
  refresh keeps old refresh_token when omitted, refresh failure THROWS with
  re-auth message. spotify_get gateway ported from Stage 0 (single network
  retry + 429 Retry-After; token handled internally). `python -m
  src.common.spotify` = one-time auth + recently-played smoke test.
- src/ingest/harvester.py — watermark file data/state/watermark.json;
  limit=50 + after=watermark; envelope {fetched_at, source:"api", payload} one
  line per item → data/raw/plays/YYYY-MM.jsonl (bucketed by played_at month,
  append-only); watermark advances ONLY after write (ADR-003); one JSON log
  line per run; empty items ⇒ log + exit 0.
- ops/com.devansh.music-analytics.harvester.plist — hourly via
  StartCalendarInterval (missed-while-asleep runs coalesce to one catch-up at
  wake, unlike StartInterval) + RunAtLoad; logs → logs/.
- tests/test_harvester.py — 8 tests, stdlib unittest, gateway mocked.
Checklist (G1):
- [x] Tests pass — evidence: `.venv/bin/python -m unittest discover -s tests -v`
      → "Ran 8 tests ... OK" (incl. watermark-not-advanced-on-persist-failure,
      crash-refetch-duplicates-not-loss, after-param-on-second-run)
- [x] secrets/.env/plays/backfill/state/logs all gitignored — evidence:
      `git check-ignore` on all six paths → all ignored ✓
- [x] GDPR export in flight → RECEIVED, in data/backfill/ (both packages;
      extended = Streaming_History_Audio_2017..2023+)
- [ ] UNVERIFIED (needs Devansh, in order): dashboard redirect URI →
      interactive auth run → tokens mode 600 check → two manual harvester runs
      (watermark proof) → watermark-reset dup test → launchd install +
      unattended run. Exact commands in session notes 2026-07-15.
Decisions made today (→ ADR refs): none ADR-worthy; module layout
(src/common/spotify.py as the single seam), port 8888, StartCalendarInterval
choice recorded here.
New QUESTION_BANK entries: none today (Q13b added 2026-07-13 covers the open
schema question).
API_NOTES updated: recently-played contract (verified 2026-07-15; endpoint
returns NO podcasts — D6 relevance); account-data vs extended filename
collision trap.
Handoff: code complete + unit-tested; NOTHING live-verified yet (no tokens
exist). Do not schedule launchd before the interactive auth succeeds.

---
## 2026-07-15 — GATE G1 PASSED (live verification by Devansh)
Model used: [FABLE session drove; Devansh executed all live steps]
Checklist:
- [x] Auth end-to-end; tokens mode 600 — evidence:
      `python -m src.common.spotify` → "Authorized. Tokens written ... (mode
      600). Smoke test: recently-played returned 1 item(s)";
      `ls -l secrets/tokens.json` → `-rw-------  1 devansh  staff  507`
- [x] git status clean of secrets; secrets/ + .env + plays + state + backfill
      all gitignored — evidence: `git check-ignore` sweep (2026-07-15) all ✓;
      status shows only source/docs files
- [x] Two consecutive manual runs, second fetches only new — evidence:
      run 1: `{"items_fetched": 44, "watermark_before": null,
      "watermark_after": 1784106024225}`
      run 2: `{"items_fetched": 0, "watermark_ms": 1784106024225,
      "note": "no new plays"}`
- [x] Kill/duplicate tolerance — evidence: `rm data/state/watermark.json` →
      rerun refetched 44 → `wc -l` = 88 lines (44 duplicated, zero lost,
      watermark identical). Ordering also pinned by unit test
      (watermark_not_advanced_when_persist_fails). Torn-line edge → Q39.
- [x] launchd installed; unattended run observed — evidence: `launchctl list`
      → `-  0  com.devansh.music-analytics.harvester`; logs/harvester.log:
      `{"fetched_at": "2026-07-15T09:02:03...", "items_fetched": 0, "note":
      "no new plays"}` (RunAtLoad, launchd-executed). NOTE: spot-check the
      first top-of-hour tick in logs/harvester.log to confirm cadence.
- [x] GDPR export — RECEIVED (better than in-flight), data/backfill/
Decisions made today (→ ADR refs): none new; ops decisions logged 2026-07-15
above.
New QUESTION_BANK entries: Q38–Q40 (kill-test equivalence, torn-line risk,
launchd scheduling semantics).
Handoff: G1 closed. Harvester is LIVE — do not break it (prime directive).
Next: Day 3 [OPUS-PLAN] — Postgres via Docker compose + schema.sql transcribed
from SCHEMA_SPEC.md + first loader.
