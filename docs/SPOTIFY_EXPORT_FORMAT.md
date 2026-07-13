# SPOTIFY_EXPORT_FORMAT.md — Extended Streaming History field reference

Verbatim reference of the "Read Me First" that shipped inside the Spotify
Extended Streaming History export (received 2026-07-12). This is the PRIMARY
SOURCE for the export-field facts recorded in API_NOTES.md ("GDPR Extended
Streaming History"). The doc itself is generic (Spotify ships the same template
to everyone) and contains no personal data; the actual `Streaming_History_*.json`
files it describes DO contain PII and live only in `data/backfill/` (gitignored).

Two stream types are documented: `end_song` and `end_video`. Each stream object
in the JSON arrays begins with `{"ts": ...`.

## Example — song stream (`end_song`)

```json
{
  "ts": "YYYY-MM-DD 13:30:30",
  "username": "…",
  "platform": "…",
  "ms_played": …,
  "conn_country": "…",
  "ip_addr_decrypted": "…",
  "user_agent_decrypted": "…",
  "master_metadata_track_name": "…",
  "master_metadata_album_artist_name": "…",
  "master_metadata_album_album_name": "…",
  "spotify_track_uri": "…",
  "episode_name": …,
  "episode_show_name": …,
  "spotify_episode_uri": …,
  "reason_start": "…",
  "reason_end": "…",
  "shuffle": null/true/false,
  "skipped": null/true/false,
  "offline": null/true/false,
  "offline_timestamp": …,
  "incognito_mode": null/true/false
}
```

The `end_video` object carries the same fields; the `episode_*` fields are
populated instead of the `master_metadata_*` / `spotify_track_uri` ones.

## Field reference (from Spotify's Read-Me)

| Field | Contains |
|---|---|
| `ts` | Timestamp when the track STOPPED playing, in UTC. Order: year, month, day, then time in 24-hour format. |
| `username` | Your Spotify username. |
| `platform` | Platform used when streaming (e.g. Android OS, Google Chromecast). |
| `ms_played` | Number of milliseconds the stream was played. |
| `conn_country` | Country code where the stream was played (e.g. SE — Sweden). |
| `ip_addr_decrypted` | IP address logged when streaming the track. |
| `user_agent_decrypted` | User agent used when streaming (e.g. a browser like Firefox or Safari). |
| `master_metadata_track_name` | Name of the track. |
| `master_metadata_album_artist_name` | Name of the artist, band, or podcast. |
| `master_metadata_album_album_name` | Name of the album of the track. |
| `spotify_track_uri` | Spotify URI uniquely identifying the track: `spotify:track:<base-62 string>`. |
| `episode_name` | Name of the podcast episode. |
| `episode_show_name` | Name of the podcast show. |
| `spotify_episode_uri` | Spotify URI uniquely identifying the podcast episode: `spotify:episode:<base-62 string>`. |
| `reason_start` | Why the track started (e.g. "trackdone"). |
| `reason_end` | Why the track ended (e.g. "endplay"). |
| `shuffle` | True/False depending on whether shuffle mode was used. |
| `skipped` | Whether the user skipped to the next song. |
| `offline` | Whether the track was played in offline mode. |
| `offline_timestamp` | Timestamp of when offline mode was used, if used. |
| `incognito_mode` | Whether the track was played during a private session. |

## Project-relevant notes (see API_NOTES.md for the ledger entries)

- `ts` is stream END, second precision, UTC — the basis for ADR-005 reconciliation.
- Music filter (D5): `spotify_track_uri` non-null AND `spotify_episode_uri` null.
  `track_id` = tail of the `spotify:track:<id>` URI.
- Only ONE artist name (`master_metadata_album_artist_name`, a string, no IDs) ⇒
  export rows cannot populate `track_artists`; that comes from the API single-track
  GET (invariant 7).
- `offline` / `offline_timestamp` / `incognito_mode` are not in the v1 `plays`
  schema — open decision, see QUESTION_BANK Q13b.
