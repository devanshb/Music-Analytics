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
