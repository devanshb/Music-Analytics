# Music-Analytics — a personal listening data warehouse

**One sentence:** Spotify's API only remembers your last 50 plays, so this
system harvests my listening continuously, merges it with my lifetime GDPR
export, enriches it from open CC0 music databases, and answers the question
*"how does my taste change over time?"* — ending each week with a self-built,
auto-generated Wrapped report.

## Why this exists
- The data is irreplaceable: a longitudinal personal dataset that cannot be
  bought or reconstructed retroactively. Ingestion continuity is the prime
  directive of the whole system.
- Spotify has been shrinking its API since Nov 2024 (audio features, popularity,
  top-tracks, batch endpoints all gone; dev apps capped at 5 users). This
  project routes around that with entity resolution into the MusicBrainz /
  ListenBrainz / AcousticBrainz ecosystem instead of pretending the endpoints
  still exist.

## Architecture (one screen)
    Spotify recently-played ──▶ harvester (hourly, watermark, at-least-once)
                                   │ append-only JSONL          [RAW — immutable]
    GDPR lifetime export ──────────┤
                                   ▼
                         loader (idempotent upserts)            [STAGING]
                                   ▼
        Postgres: plays ▪ tracks ▪ albums ▪ artists ▪ track_artists
                                   ▼
      enrichment: ISRC → MusicBrainz MBID → genres ▪ (Phase 2: LB popularity,
      AB audio features)                                         [DIMS+]
                                   ▼
      metrics layer: sessions ▪ discovery rate ▪ genre entropy ▪ taste drift
      ▪ resurrections ▪ listening clock                          [MARTS]
                                   ▼
      Weekly Wrapped (static HTML) ▪ (Phase 2: LLM narration + text-to-SQL Q&A
      through a SELECT-only role) ▪ (Phase 2: client-side public analyzer)

## Doc map
| You want | Read |
|---|---|
| The plan, gates, day-by-day sprint | ROADMAP.md |
| Operating rules for Claude sessions | CLAUDE.md |
| Verified external-API facts | API_NOTES.md |
| Schema definition | docs/SCHEMA_SPEC.md |
| Metric semantics | docs/METRIC_DEFINITIONS.md |
| Every decision + why | docs/adr/ |
| Data sources + admission rule | docs/DATA_SOURCES.md |
| Model routing (Opus/Sonnet/Fable) | docs/MODEL_ROUTING.md |
| Gate evidence | PROGRESS.md |
| Interview prep | docs/INTERVIEW_DEFENSE.md, docs/QUESTION_BANK.md |

## Honest limitations (kept current on purpose)
Single-user by design (Spotify dev mode caps at 5 authorized users; extended
quota requires a 250k-MAU business). Laptop scheduling can gap until the
GitHub Actions harvester (T0) lands. AcousticBrainz features are frozen at 2022
and used as relative trend signals only. All of these are discussed, not hidden,
in docs/INTERVIEW_DEFENSE.md.
