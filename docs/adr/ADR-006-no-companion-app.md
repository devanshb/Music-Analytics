# ADR-006: No mobile companion app
Date: 2026-07-11 · Status: Accepted
Model context: Devansh proposed skipping; Fable 5 corrected the premise

## Context
Idea: iOS/Android app "so phone/tablet listening still counts as datapoints."

## Decision
No companion app, ever, for capture purposes.

## Alternatives considered
- Build it — rejected on a FALSE PREMISE: the harvester polls Spotify's
  SERVER-SIDE recently-played API, which already contains plays from every
  device on the account (phone, tablet, speaker, car). A mobile app adds zero
  data. Original effort-vs-reward instinct was right; the architectural reason
  is the one to say in interviews.
- Capture non-Spotify listening (YouTube, local files) — real gap, already
  solved by existing scrobblers submitting to ListenBrainz; if ever wanted,
  configure one (T2 adjacency), don't write one.

## Consequences
All effort stays on the warehouse and web artifacts. Revisit trigger: none for
capture; a read-only mobile VIEW of Wrapped could exist someday but is
explicitly unplanned.
