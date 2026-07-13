# FABLE_REVIEW.md — monthly frontier-model audit protocol

Purpose: once a month, a Fable-class session audits what the daily executors
cannot see about themselves: architecture drift, invariant erosion, quality
decay, dishonest gate evidence. Fable is an AUDITOR here, not an executor —
its output is findings + a prioritized correction list, not code.

## Prep (Sonnet does this the day before; ~30 min)
Assemble docs/fable_briefing_<YYYY-MM>.md containing:
1. PROGRESS.md tail since last review (verbatim, not summarized).
2. `git log --oneline` since last review + diff STATS (not full diffs).
3. Current CLAUDE.md, ROADMAP position, list of ADRs added/changed.
4. The three ugliest things (executor's own confession — mandatory section;
   an empty confession section invalidates the briefing).
5. Any gate evidence Devansh doubts.
6. Open QUESTION_BANK entries without answers.
Anti-flattery rule: the briefing is evidence, not a pitch. Fable's first task
is to probe whatever the briefing seems to be steering around.

## The audit (Fable session, one shot — context is precious)
Checklist:
- Invariants 1–14 (CLAUDE.md): sample the code paths that touch each; name violations.
- Gate evidence: pick 2 gates at random; is the pasted evidence reproducible?
- Drift scan: features not on ROADMAP? fallbacks? new deps without ADR? raw-zone writes?
- ADR hygiene: decisions made without ADRs (check PROGRESS + git log against docs/adr/).
- QUESTION_BANK: answer quality spot-check — would these survive a real interviewer?
- Doc rot: CLAUDE.md stale notes, API_NOTES entries past staleness window.
- MODEL_ROUTING: re-verify plan/limit facts (they change); update the doc.
Output format: findings ranked P0/P1/P2, each with file:line or doc pointer and
a one-line correction. P0s become the next day's ROADMAP block.

## Log
| date | model | P0s | P1s | notes |
|---|---|---|---|---|
| 2026-07-11 | Fable 5 | — | — | Architecture session; scaffold generated (baseline). |
