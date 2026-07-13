# SKILLS.md — skill taxonomy and rules

Skills live at .claude/skills/<name>/SKILL.md (project-level, shared via git).
Each skill = one complete, self-contained domain. The frontmatter description
is the TRIGGER, not documentation — it must contain the phrases a session would
actually use. Body <150 lines here (official ceiling is 500); heavy reference
belongs in the repo docs the skill points to, not inside the skill.

## The six domains
| skill | domain | fires when a session touches... |
|---|---|---|
| spotify-api | auth, harvester, gateway, Spotify quirks | OAuth, tokens, recently-played, fetchers, 401/429 |
| pipeline-ops | scheduling, heartbeats, gaps, DQ, raw zone | launchd/Actions, missed runs, gap analysis, data-quality failures |
| warehouse-sql | schema, loaders, idempotency, psycopg | tables, upserts, migrations, ingest_ledger, "add a column" |
| brainz-enrichment | MB/LB/AB clients, entity resolution | ISRC, MBID, genres, popularity, audio features, rate politeness |
| metrics-reporting | metric definitions, marts, Wrapped, LLM layer | new metric, fixtures, report rendering, narration, text-to-SQL |
| project-governance | gates, ADRs, question bank, model routing, reviews | finishing a stage, making a decision, "is this done", escalation |

## Anti-sprawl rules
1. New skill only when a domain recurs across ≥3 sessions AND fits none above —
   and it needs an ADR-lite note in the skill itself explaining why it exists.
2. A skill never duplicates a truth doc; it POINTS (API_NOTES, SCHEMA_SPEC,
   METRIC_DEFINITIONS are the sources; skills are the procedures).
3. If a skill misfires or never fires, fix the DESCRIPTION first (trigger
   phrases), body second. /doctor diagnoses non-triggering skills.
4. Review skill health at every [FABLE-REVIEW]; delete dead skills.
