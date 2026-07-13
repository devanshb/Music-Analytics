# ADR-007: Public analyzer is client-side only
Date: 2026-07-11 · Status: Accepted (binds T5)
Model context: Fable 5 architecture session; Devansh approved

## Context
T5 lets anyone analyze their own GDPR export. Exports contain IP addresses and
location history — hosting strangers' uploads makes us a data controller with
GDPR obligations. Separately, invariant 11 bars multi-user SPOTIFY-API features;
a file-processing app does not touch the Spotify API and is therefore allowed.

## Decision
The analyzer is a static site. Parsing + SQL run entirely in-browser (Web
Worker + DuckDB-WASM). HARD INVARIANTS: no upload endpoint exists; no
server-side processing of anyone's export; no analytics that transmit listen
data. Metric SQL is SHARED with the warehouse (write once, run in Postgres and
in the browser).

## Alternatives considered
- Server-side processing "for better UX" — rejected: custody, liability,
  hosting cost, and it deletes the privacy differentiator vs stats.fm.
- Don't build T5 — viable, but forfeits the strongest share-with-the-world
  artifact that Spotify's platform rules actually permit.

## Consequences
Browser memory/perf constraints on 100MB+ zips become a real (and
interview-rich) engineering problem. Gate T5 requires network-tab proof of
zero egress. Revisit trigger: none — client-side-only IS the product.
