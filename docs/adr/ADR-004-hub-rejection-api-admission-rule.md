# ADR-004: "Music hub" rejected → API admission rule
Date: 2026-07-11 · Status: Accepted
Model context: Fable 5 architecture session; Devansh approved after debate

## Context
Proposal: public multi-API hub (artist info, tabs, links, trivia chatbot) for
site visitors. Evaluated against interview defensibility and platform reality.

## Decision
Rejected. Standing rule instead: an external API is admitted ONLY if it joins
the warehouse on an existing entity (artist/track/ISRC/MBID) AND powers a
metric or report feature. Registry: docs/DATA_SOURCES.md.

## Alternatives considered
- Build the hub — rejected: no hard problem (additive integrations), personal
  API keys serving strangers (ToS/quota/abuse), most listed APIs are enterprise
  or paid, lyrics are a licensing minefield, generic trivia-RAG has no
  defensible corpus. Steelman: breadth demos fast — but breadth without depth
  is exactly what harsh interviews punish.
- Hub pointed INWARD — accepted in pieces: LLM-over-warehouse (T1), LB (T2),
  concert radar (T4), link garnish.

## Consequences
Every future "let's add API X" conversation starts at the admission rule.
Do not relitigate without new facts; executors proposing hub-shaped features
are drifting. Revisit trigger: Spotify materially reopens its platform.
