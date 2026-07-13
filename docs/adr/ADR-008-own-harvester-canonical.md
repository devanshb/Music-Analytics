# ADR-008: Own harvester canonical; ListenBrainz import is not capture
Date: 2026-07-11 · Status: Accepted (binds T2)
Model context: Fable 5 architecture session; Devansh approved

## Context
ListenBrainz offers built-in Spotify listen importing. Tempting: outsource
capture, delete the harvester.

## Decision
Our harvester remains the sole canonical capture path. LB receives SUBMISSIONS
from the warehouse (T2a, batch submitter — never wired into the harvester
itself); LB is also CONSUMED for community popularity/similarity (T2b).

## Alternatives considered
- LB import as primary capture — rejected: outsources the prime directive to a
  third party subject to the same shrinking Spotify platform; we'd own neither
  the raw payloads nor the failure modes; and "I configured an importer" is
  not an interview story.
- LB import as a redundant secondary feed — rejected: violates no-backups /
  one-canonical-path principles and creates a second reconciliation problem
  for marginal safety.

## Consequences
Harvester reliability work (heartbeats, T0 Actions) stays mandatory. LB profile
becomes a public living demo of the pipeline. Revisit trigger: Spotify revokes
this app's access entirely (then LB import becomes the survival path — note
that in INTERVIEW_DEFENSE narrative 4 territory, Q14).
