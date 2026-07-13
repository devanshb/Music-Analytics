# ADRs — Architecture Decision Records

Any decision that changes what gets built, in what order, or on what invariant
gets an ADR — BEFORE or WITH the implementing commit, never after-the-fact
archaeology. Executors: making an ADR-worthy decision without writing the ADR
is drift; the project-governance skill defines "ADR-worthy".

Format: TEMPLATE.md. Keep each under ~30 lines. Statuses: Proposed → Accepted →
(Superseded by ADR-NNN). Never edit an Accepted ADR's decision — supersede it.
Number sequentially; filename ADR-NNN-kebab-title.md.

Index
- 001 Capture-first ordering (Accepted)
- 002 Postgres over SQLite (Accepted)
- 003 At-least-once capture + idempotent load (Accepted)
- 004 Music-hub rejection → API admission rule (Accepted)
- 005 Export-wins reconciliation (Proposed — finalize with D6 measurements)
- 006 No mobile companion app (Accepted)
- 007 Public analyzer is client-side only (Accepted, binds T5)
- 008 Own harvester canonical over ListenBrainz import (Accepted, binds T2)
