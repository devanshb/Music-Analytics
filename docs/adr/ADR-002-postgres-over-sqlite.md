# ADR-002: Postgres over SQLite
Date: 2026-07-11 · Status: Accepted
Model context: Fable 5 architecture session; Devansh approved

## Context
Single-user local warehouse. SQLite would genuinely suffice functionally.

## Decision
PostgreSQL 16 (Docker, pinned), raw SQL via psycopg 3.

## Alternatives considered
- SQLite — sufficient, simpler ops. Rejected for deliberate production parity:
  ON CONFLICT upserts, timestamptz, ROLES (the T1 SELECT-only LLM guardrail
  depends on roles existing), and interview relevance. We say the first
  sentence of this ADR out loud in interviews.
- DuckDB — superb analytics, but weaker as the system-of-record for
  concurrent writer jobs; reappears client-side in T5 (DuckDB-WASM).

## Consequences
Docker becomes a dependency (accepted; one pinned service). Role-based LLM
guardrail is now possible. Revisit trigger: none foreseeable.
