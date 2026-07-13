# DATA_SOURCES.md — source registry

Every external source must pass the API admission rule (ADR-004): it joins the
warehouse on an existing entity (artist / track / ISRC / MBID) AND powers a
metric or report feature. This file is the registry; adding a source without a
row here (and an ADR if non-trivial) is drift.

## Admitted

| Source | Joins on | Powers | License/cost | Rate rules | Status |
|---|---|---|---|---|---|
| Spotify Web API | — (origin) | plays, dims | ToS; dev mode | 30s window; honor Retry-After | Core; shrinking — see API_NOTES |
| GDPR extended export | spotify_track_uri | lifetime backfill, ms_played/skip metrics | your own data | one-time | Core (Stage/Day 5) |
| MusicBrainz | ISRC → recording MBID | genres, artist metadata; unlocks all Brainz joins | CC BY-NC-SA data, free API | 1 req/s, real UA + email | Sprint D8–9 |
| ListenBrainz (submit) | MBID/spotify_id from warehouse | public profile = living demo; community contribution | CC0 (your listens become public — deliberate) | token auth; ~"half or 4 min" listen rule | Phase 2 T2a |
| ListenBrainz (consume) | artist/recording MBID | mainstreamness, contrarian index, discovered-before-crowd; popularity substitute for what Spotify deleted | CC0 | honor rate headers | Phase 2 T2b |
| AcousticBrainz | recording MBID | energy/valence-proxy/BPM era trends | CC0 | ~1 req/s, batch ≤25, X-RateLimit-* headers | Phase 2 T3; API=verify-at-build; frozen 2022; dump is the fallback (that switch = ADR) |
| Bandsintown OR Ticketmaster (pick ONE) | artist name (⚠ name-match risk → mismatch table) | concert radar in Wrapped | free tier | cache weekly | Phase 2 T4 |
| Odesli/song.link | spotify track id | cross-platform links (garnish only) | free | trivial | Anytime post-GX; never demoed |

## Evaluated and REJECTED (do not relitigate without new facts + ADR)

| Source | Why rejected |
|---|---|
| Soundcharts, Chartmetric, Gracenote, Music Story, TiVo, Songstats | Enterprise B2B / sales-gated. Out of reach; also fail "powers a metric" for personal data. |
| Musixmatch / Genius / any lyrics API | Lyrics licensing minefield; Genius API doesn't return lyrics anyway. Permanently out of scope. |
| Last.fm tags | Second genre source violates one-way principle while MB coverage is unmeasured. Revisit ONLY if MB genre coverage <80% after T2 (would be a replacement ADR, not an addition). |
| Deezer/Apple/Amazon/YouTube catalog APIs | No warehouse join advantage over MB; auth/ToS friction. (Deezer/iTunes 30s previews may reappear narrowly inside T3b as analysis input — verify-at-build.) |
| Discogs / TheAudioDB / Cover Art Archive | Nice-to-have imagery/metadata; fails "powers a metric". CAA may garnish Wrapped art via MBID later — garnish tier, no ADR needed, no interview airtime. |
| FreqBlog & similar paid audio-feature APIs | Paid, unverifiable quality, replaces a CC0 path we already have. |
| Generic "music hub" aggregation of the above | Root rejection — see ADR-004. |

## Notes on the ListenBrainz relationship
LB is the community-scale sibling of this project. Position it that way in
interviews: we CONTRIBUTE listens under CC0 (public LB profile doubles as a live
demo of the pipeline) and CONSUME the community corpus as the popularity/trend
signal Spotify removed. Their built-in Spotify importer exists but is NOT our
capture path (ADR-008): it inherits the same Spotify constraints, and the prime
directive — owning capture — is not outsourced.
