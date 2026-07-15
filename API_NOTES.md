# API_NOTES.md — ledger of VERIFIED external-API facts

Protocol (CLAUDE.md): design/code only against facts recorded here or verified
this session against official docs (then recorded here in the same change).
Each entry: FACT · VERIFIED date · SOURCE. Spotify facts >~3 months old are
stale — re-verify before depending on them.

## Spotify Web API
- Dev Mode (Feb 2026): Premium required; 1 Client ID; ≤5 authorized users.
  Extended quota = registered business + 250k MAU. [2026-07-11 · developer.spotify.com blog 2026-02-06 + quota-modes doc]
- Removed for dev mode (Feb 2026 wave): artist top-tracks, new-releases,
  available markets, batch metadata endpoints, other users' profiles/playlists,
  popularity fields, album label; search limit max = 10. [2026-07-11 · web-api changelog feb-2026 + migration guide]
- Spotify statement: moving away from Client Credentials for metadata ⇒ OAuth
  Authorization Code is this project's only auth path. [2026-07-11 · changelog/community]
- external_ids (ISRC): removed Feb 2026, REVERTED Mar 2026 — currently
  available; VOLATILE, re-verify at Day 8. [2026-07-11 · changelog mar-2026]
- Redirect URIs: HTTPS or loopback literal http://127.0.0.1:PORT (not
  localhost). [2026-07-11 · insecure-redirect-URI migration doc]
- Authorization Code flow mechanics: GET accounts.spotify.com/authorize with
  client_id, response_type=code, redirect_uri (required) + state, scope
  (optional — we always send state). Token exchange: POST
  accounts.spotify.com/api/token, form-encoded, grant_type=authorization_code
  + code + redirect_uri; client auths via `Authorization: Basic
  base64(client_id:client_secret)` header. Response: access_token,
  token_type=Bearer, scope, expires_in (3600), refresh_token.
  [2026-07-12 · developer.spotify.com tutorials/code-flow]
- Token refresh: same token endpoint, grant_type=refresh_token +
  refresh_token, same Basic header. Response MAY omit refresh_token — keep
  using the existing one when absent (rotation is not consistent). Refresh
  tokens live ~6 months from initial authorization ⇒ an unused harvester
  eventually needs a full re-auth. [2026-07-12 · tutorials/refreshing-tokens]
- recently-played: 50-item ring buffer; `after` cursor in epoch ms. Community
  reports (Mar 2026) of played_at accuracy glitches ⇒ DQ checks watch for
  duplicate/misordered timestamps. [2026-07-11 · docs + community thread]
- Rate limiting: rolling ~30s window; on 429 honor Retry-After (implemented in
  spotify_get). [carried from Stage 0, re-verified 2026-07-11]
- Established gotchas (Stage 0, still true): pagination stops on EMPTY ITEMS
  (next/total unreliable); malformed IDs → 401 not 404; include_groups noise;
  release_date_precision varies ⇒ year = [:4] slice.
- recently-played contract: GET /me/player/recently-played, scope
  user-read-recently-played. Params: limit (default 20, max 50), after/before
  (epoch MILLISECONDS, mutually exclusive). Response: items[] of
  {track (full object incl. id/name/album/artists/duration_ms/explicit),
  played_at (ISO-8601 UTC datetime), context}; cursors.{after,before}.
  Endpoint does NOT return podcast episodes at all ⇒ the API tail is
  music-only while the export includes podcasts — remember at D6
  reconciliation. [2026-07-15 · reference/get-recently-played]

## GDPR Extended Streaming History (export)
- Request at account privacy page; policy says ≤30 days, often hours–days.
- ⚠ Filename collision between the TWO packages: the plain Account-data zip
  contains `StreamingHistory_music_0.json` (LAST YEAR ONLY, fewer fields);
  the Extended package contains `Streaming_History_Audio_<years>.json`
  (lifetime). D5 must glob `Streaming_History_Audio_*.json` ONLY — the
  similarly-named account-data file is a trap. [2026-07-15 · both zips in hand,
  unpacked side-by-side in data/backfill/]
- Zip of Streaming_History_*.json arrays. Two stream types documented:
  `end_song` and `end_video` ⇒ a Video file may exist alongside Audio; do NOT
  assume Audio-only. Verified against the export's own Read-Me on receipt.
  [2026-07-13 · Spotify export "Read Me First" in hand]
- Exact field names (from the Read-Me, authoritative): ts, username, platform,
  ms_played, conn_country, ip_addr_decrypted, user_agent_decrypted,
  master_metadata_track_name, master_metadata_album_artist_name,
  master_metadata_album_album_name, spotify_track_uri, episode_name,
  episode_show_name, spotify_episode_uri, reason_start, reason_end, shuffle,
  skipped, offline, offline_timestamp, incognito_mode. ts = UTC, second
  precision, stream END. skipped is nullable (null/true/false).
  [2026-07-13 · Read Me First]
- Music vs non-music filter (D5): keep rows where spotify_track_uri is non-null
  AND spotify_episode_uri is null. track_id = tail of "spotify:track:<id>".
- ⚠ Export gives ONE artist name only (master_metadata_album_artist_name) — the
  ALBUM artist, as a string, no artist IDs, no featured artists. Export rows
  therefore CANNOT populate track_artists (invariant 7); the many-to-many list
  comes only from the API single-track GET (D5 resumable job). [2026-07-13]
- ⚠ PII beyond IP: ip_addr_decrypted, user_agent_decrypted, username are all
  personal data ⇒ never commit; never process other people's exports
  server-side (ADR-007). Lives only in data/backfill/ (gitignored).

## MusicBrainz
- ~1 req/s per client; REQUIRED meaningful User-Agent with contact info.
- Recording lookup by ISRC: /ws/2/recording?query=isrc:<isrc>&fmt=json;
  genre/tag includes on recording+artist fetch. [2026-07-11 · MB API docs]

## ListenBrainz  [verified 2026-07-11 · listenbrainz.readthedocs.io (docs build Jul 2026)]
- Auth: user token in `Authorization: Token <t>` header.
- POST /1/submit-listens; listen_type single|import|playing_now. Submission
  norm: listened to half the track or 4 minutes, whichever is lower.
- Listen payload supports additional_info incl. spotify_id, isrc,
  recording_mbid ⇒ direct mapping from warehouse.
- Popularity: POST endpoints returning total_listen_count + total_user_count
  per artist_mbid / recording_mbid (batched, order-preserving, nulls for
  unknown). Sitewide top artists/recordings endpoints exist. Similar-artists
  via LB radio artist endpoint (recording_mbid + similar_artist_mbid +
  total_listen_count).
- User listen data is public under CC0 once submitted — deliberate choice (T2a).

## AcousticBrainz  [verified 2026-07-11 · acousticbrainz.readthedocs.io + metabrainz blog + 2024 usage reports]
- STATUS: submissions ended 2022; corpus FROZEN at ~June 2022. MetaBrainz
  announced eventual site shutdown; API observed working as late as Dec 2024;
  conflicting third-party claims in 2026 ⇒ VERIFY-AT-BUILD with one curl at T3
  start. Full dump remains downloadable (fallback path; switching to it = ADR).
- API (if up): GET high-level/low-level by recording MBID; batch ≤25 MBIDs;
  rate limited via X-RateLimit-* headers (~10 req/10s observed), 429 +
  X-RateLimit-Reset-In. Unknown MBIDs silently omitted from responses.
- Data quality: MetaBrainz's own post-mortem judged the data too noisy for
  absolute use ⇒ this project uses it for RELATIVE trends only.
- License: CC0.

## Verify-at-build TODO (do not design against these until checked)
- [ ] AcousticBrainz API liveness (T3 start)
- [ ] external_ids.isrc still present (Day 8 morning)
- [ ] Bandsintown vs Ticketmaster free-tier terms (T4 start)
- [ ] Deezer/iTunes 30s preview availability + ToS for local analysis (T3b only)
- [ ] Essentia vs librosa install feasibility on this macOS (T3b only)
- [ ] DuckDB-WASM zip/JSON ingestion pattern in Web Worker (T5 start)
