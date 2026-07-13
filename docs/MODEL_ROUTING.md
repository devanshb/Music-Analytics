# MODEL_ROUTING.md — which Claude for which task

Verified against official Anthropic docs/support + recent secondary sources on
2026-07-11. Plans and limits change often — the ground truth for THIS account is
`/model`, `/usage`, `/cost` inside Claude Code and Settings → Usage on claude.ai.
Re-verify this doc at every [FABLE-REVIEW].

## Current model lineup (July 2026)
- **Fable 5** — frontier tier above Opus. Used here ONLY for monthly architecture
  reviews ([FABLE-REVIEW], see docs/FABLE_REVIEW.md). Not an executor.
- **Opus 4.8** — strongest generally available executor. Planner + hard problems.
- **Sonnet 4.6 / Sonnet 5** — default executor (Sonnet 5 needs Claude Code
  v2.1.197+; use whichever /model offers as current sonnet).
- **Haiku 4.5** — mechanical micro-tasks only; rarely worth the context churn here.

API list prices (reference only; Devansh works on subscription):
Haiku $1/$5 · Sonnet 4.6 $3/$15 · Opus 4.8 $5/$25 · Fable 5 $10/$50 per MTok.
Directional cost intuition: Opus burns roughly several × Sonnet per turn.

## Plan facts that matter (verified July 2026)
- Usage is ONE POOL across claude.ai chat, Claude Code, and Desktop/Cowork.
  Heavy daytime chat eats the same budget as Claude Code.
- Limits = 5-hour rolling session window + weekly cap(s). Max tiers carry two
  weekly buckets (all-models and a Sonnet-only bucket). Check reset times in
  Settings → Usage; Anthropic publishes multipliers, not token numbers.
- May 6, 2026: 5-hour limits doubled for Pro/Max; peak-hour throttling removed.
- Pro ($20/mo): includes Claude Code and (per current reporting) Opus 4.8 access
  with tight practical headroom — VERIFY on this account with /model. Pro is
  fine for planning + light execution; a 12h/day sprint will hit its walls.
- Max 5x ($100/mo): 5× Pro per-session usage. **Sprint recommendation: switch to
  Max 5x for the 14 days.** If Opus still caps mid-sprint, escalate to Max 20x
  for one month rather than starving the plan phase.
- June 15, 2026 change: PROGRAMMATIC usage (`claude -p`, Agent SDK, GitHub
  Actions running Claude) bills to a separate monthly credit pool ($20 Pro /
  $100 Max 5x). ⇒ **Never wire `claude -p` into cron/Actions for this project.**
  The T0 Actions harvester runs plain Python — zero Claude usage — by design.

## The decision tree (apply per task; tags in ROADMAP are pre-routed)

1. Is it a MONTHLY ARCHITECTURE AUDIT? → **[FABLE-REVIEW]** (docs/FABLE_REVIEW.md).
2. Does the task CREATE OR CHANGE any of: schema, auth flow, watermark logic,
   reconciliation semantics, LLM guardrails, an ADR-level decision, or a
   multi-module plan? → **Opus plans** (plan mode / `/model opusplan`), then
   **Sonnet executes** the approved plan. This is Anthropic's own recommended
   pattern: the highest-value Opus tokens are the plan.
3. Is it implementation against an existing spec, tests, fixtures, docs, SQL
   transcription from SCHEMA_SPEC/METRIC_DEFINITIONS, report templating?
   → **Sonnet**, default effort. No Opus.
4. Is it purely mechanical (rename, boilerplate, log line, regex explain)?
   → **Haiku** if convenient, else Sonnet. Never spend Opus here.
5. Is Sonnet STUCK? Escalation tripwires (also in CLAUDE.md): two failed
   attempts at one bug · plan no longer matches reality · about to guess an API
   behavior · cross-cutting debugging spanning >3 modules. → Stop; half-page
   state summary; **Opus** takes the wheel for diagnosis; Sonnet resumes after.

## Effort + context discipline (stretches every plan tier)
- Default effort for execution; raise effort/thinking only for the Opus planning
  or gnarly-debug moments — thinking tokens bill as output.
- `/clear` between unrelated tasks (single most effective usage lever);
  `/compact` mid-task when context bloats. Long uncleared sessions are the #1
  cause of surprise limit hits.
- Stable context belongs in CLAUDE.md / skills (cache-discounted), not re-pasted
  prompts. Point sessions at specific files; don't let the agent trawl the repo.
- Batch related questions into one turn.

## Sprint-day budget pattern (Max 5x assumption)
Morning: one Opus planning block (plan mode; approve; /clear).
Day: Sonnet execution sessions, /clear at each task boundary.
Evening: Sonnet for verification + PROGRESS/QUESTION_BANK updates.
If the weekly Opus/all-model bucket nears empty: planning quality degrades
first — protect Opus tokens by writing better briefs, not by skipping plans.

## What each model is bad at HERE (pre-empt, don't discover)
- **Sonnet:** overconfident API recall (⇒ API_NOTES protocol is mandatory);
  scope creep into Phase-2 features mid-sprint (⇒ gates); quietly adding
  fallbacks/defensive code (⇒ prohibited list); "should work" completions
  (⇒ verification standard).
- **Opus:** over-architecting (queues, orchestrators, abstractions this project
  explicitly rejects — the no-overengineering principle applies to it too);
  expensive drift in long sessions (⇒ plan, hand off, /clear).
- **Both:** confidently misremembering Spotify's post-2026 API surface; treating
  ROADMAP order as suggestions; editing raw-zone files "to fix data".
- **Fable (monthly):** context is one-shot — it only sees what the briefing
  shows it. The FABLE_REVIEW prep checklist exists so the audit isn't blinded
  by a flattering summary.
