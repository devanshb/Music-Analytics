# METRIC_DEFINITIONS.md — metric semantics (also the LLM grounding corpus)

Rules: every metric gets (1) a plain-English definition ≤2 sentences a
non-engineer understands, (2) exact parameters, (3) a view name, (4) one fixture
test with hand-computed expected output. This file is handed verbatim to the
T1 LLM features — write definitions as if a model will take them literally,
because one will. Changing a definition ⇒ re-run the T1 eval set.

## qualified_play (the foundation — what counts as "a play")
A play qualifies if ms_played ≥ 30000, OR the row came from the API (source=
'api'), which carries no duration and counts by presence. Raw keeps everything;
qualification happens only here. View: v_qualified_plays.

## Sessions
A session is a run of qualified plays where each gap to the previous play is
≤ 30 minutes; a longer gap starts a new session. Derived: session length,
plays/session, start-hour distribution. View: v_sessions (LAG over played_at).

## Discovery rate
For each ISO week, the share of qualified plays that are the FIRST-EVER play of
that track in the whole warehouse. Measures how much listening is new vs
familiar. View: v_discovery_weekly.

## Genre entropy (monthly)
Shannon entropy of the distribution of qualified plays across genres within a
calendar month (multi-genre tracks contribute fractionally, 1/n per genre).
Higher = more diverse month. View: v_genre_entropy_monthly.

## Taste drift (monthly)
Represent each month as a normalized artist-play vector over qualified plays;
drift(month) = 1 − cosine_similarity(month, previous month). Spikes = taste
ruptures. Thin Python allowed for the cosine step. View/table: v_taste_drift.

## Skip behavior (export-era rows only)
Skip rate = skipped plays / plays, sliced by shuffle on/off, reason_start, and
track age since first play. NULL skipped rows are excluded, not counted false.
View: v_skip_behavior.

## Resurrections + nostalgia index
A resurrection is a qualified play of a track whose previous qualified play was
≥ 180 days earlier. Nostalgia index (monthly) = share of qualified plays on
tracks first discovered > 2 years before the play. Views: v_resurrections,
v_nostalgia_monthly.

## Listening clock
Qualified-play counts by (hour-of-day × weekday) in the USER'S LOCAL timezone —
the one metric family where conversion from UTC happens, at query time,
explicitly. Also: platform share by year (export platform field).
View: v_listening_clock, v_platform_years.

## Phase 2 definitions (added when tracks start — placeholders)
- Mainstreamness score / contrarian index / discovered-before-the-crowd (T2b)
- Energy / valence-proxy / BPM era trends + coverage-by-release-year (T3)
- Era assignments from clustering (T6)
