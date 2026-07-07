import requests
import dotenv
import os
import json
import csv
import time
import argparse

dotenv.load_dotenv()

client_id = os.getenv("SPOTIFY_CLIENT_ID")
client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")

if not client_id or not client_secret:
    raise RuntimeError("SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET must be set in .env")

# Without a timeout, requests can hang forever on a dead connection — which is
# the opposite of failing fast, and would make the network retry below pointless
# (a hang never becomes a catchable Timeout). One constant, used on every call.
REQUEST_TIMEOUT = 10  # seconds

# ---------- External world: auth + HTTP ----------

def get_access_token():
    response = requests.post(
        "https://accounts.spotify.com/api/token",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret
        },
        timeout=REQUEST_TIMEOUT
    )
    if not response.ok:
        raise RuntimeError(f"Failed to get access token: {response.text}")
    return response.json()["access_token"]


# Attaches the Bearer header and makes the GET. Handles two DISTINCT failure
# categories separately, on purpose:
#   1. transient network failure (connection dropped, timeout) -> retry once
#   2. HTTP 429 rate limit (server answered, said slow down)   -> wait + retry
# They mean different things, so blurring them into one catch-all would hide
# *why* a call failed. Anything past one retry is allowed to raise.
def spotify_get(path, access_token, params=None):
    url = f"https://api.spotify.com/v1/{path}"
    headers = {"Authorization": f"Bearer {access_token}"}

    try:
        response = requests.get(url, headers=headers, params=params, timeout=REQUEST_TIMEOUT)
    except requests.exceptions.RequestException as e:
        # Log the exception TYPE and path only — never headers (Bearer token).
        print(f"Network error on {path} ({type(e).__name__}), retrying once")
        time.sleep(2)
        response = requests.get(url, headers=headers, params=params, timeout=REQUEST_TIMEOUT)

    if response.status_code == 429:
        wait_seconds = int(response.headers.get("Retry-After", 1))
        time.sleep(wait_seconds)
        response = requests.get(url, headers=headers, params=params, timeout=REQUEST_TIMEOUT)

    if not response.ok:
        raise RuntimeError(f"Spotify API error: {response.text}")
    return response.json()


# Generic pagination helper — walks offset forward until a page comes back
# empty. Does NOT trust "next" or "total" (Spotify has a known bug where "next"
# points past the real end), so an empty items page is the only stop signal.
# max_pages is a fail-fast backstop against a runaway loop.
def paginate(path, token, params, max_pages=50):
    all_items = []
    offset = 0
    limit = params["limit"]
    pages_fetched = 0

    while True:
        page_params = dict(params)
        page_params["offset"] = offset
        page = spotify_get(path, token, page_params)
        items = page["items"]

        if not items:
            break

        all_items.extend(items)
        offset += limit
        pages_fetched += 1

        if pages_fetched >= max_pages:
            raise RuntimeError(f"Pagination exceeded max_pages ({max_pages}) for: {path}")

    return all_items


# ---------- External world: provider fetchers for Spotify API ----------

def search_artist_id(name, token):
    response = spotify_get("search", token, {"q": f"artist:{name}", "type": "artist"})
    if not response["artists"]["items"]:
        raise RuntimeError(f"Artist not found: {name}")
    return response["artists"]["items"][0]["id"]


def fetch_artist_albums(artist_id, token):
    return paginate(f"artists/{artist_id}/albums", token, {"include_groups": "album", "limit": 10})


def fetch_album_tracks(album_id, token):
    return paginate(f"albums/{album_id}/tracks", token, {"limit": 50})


# ---------- Normalization Layer ----------

# "id" is renamed to "album_id" — this is the foreign key that track records
# point back to, so naming it explicitly now sets up the Stage 3 DB relationship.
# release_date_precision rides along as a guardrail: any future code that parses
# release_date as a full date can check it first instead of crashing on a
# year-only or month-only value.
def normalize_album(raw_album):
    return {
        "album_id": raw_album["id"],
        "album_name": raw_album["name"],
        "album_type": raw_album["album_type"],
        "total_tracks": raw_album["total_tracks"],
        "release_date": raw_album["release_date"],
        "release_date_precision": raw_album["release_date_precision"],
    }


# Now carries the track's own id/uri, its disc_number, and its artist ids, plus
# the album_id foreign key threaded in from the loop. A track can have multiple
# artists (features), and a CSV cell can't hold a real list, so artist_ids is
# joined into a ";"-delimited string — a deliberate flattening compromise that
# Stage 3 will replace with a proper track-to-artist join table.
def normalize_album_tracklist(raw_track_list, album_id, album_name, release_date):
    tracks = []
    for track in raw_track_list:
        artist_ids = []
        for artist in track["artists"]:
            artist_ids.append(artist["id"])

        tracks.append({
            "track_id": track["id"],
            "uri": track["uri"],
            "name": track["name"],
            "duration_ms": track["duration_ms"],
            "explicit": track["explicit"],
            "track_number": track["track_number"],
            "disc_number": track["disc_number"],
            "album_id": album_id,
            "album_name": album_name,
            "release_date": release_date,
            "artist_ids": ";".join(artist_ids),
        })
    return tracks


# ---------- Deduplication ----------

def canonical_title(album_name):
    cut_at = len(album_name)
    for bracket in ["(", "["]:
        idx = album_name.find(bracket)
        if idx != -1:
            cut_at = min(cut_at, idx)
    return album_name[:cut_at].strip().lower()


def dedup_albums(albums):
    groups = {}
    for album in albums:
        key = canonical_title(album["album_name"])
        groups.setdefault(key, []).append(album)

    canonical_list = []
    for variants in groups.values():
        canonical = min(variants, key=lambda a: (a["release_date"], a["total_tracks"]))
        canonical_list.append(canonical)

    return sorted(canonical_list, key=lambda a: a["release_date"])


# ---------- Internal world: output ----------

def save_json(data, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def write_csv(records, path):
    if not records:
        raise RuntimeError("No records to write")
    fieldnames = list(records[0].keys())
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)


# ---------- Internal world: analytics ----------

def album_with_most_tracks(albums):
    return max(albums, key=lambda a: a["total_tracks"])


def longest_tracks(tracks, n):
    return sorted(tracks, key=lambda t: t["duration_ms"], reverse=True)[:n]


def shortest_tracks(tracks, n):
    return sorted(tracks, key=lambda t: t["duration_ms"])[:n]


def total_runtime_by_album(tracks):
    totals = {}
    for t in tracks:
        name = t["album_name"]
        if name not in totals:
            totals[name] = 0
        totals[name] += t["duration_ms"]
    return totals


def explicit_tracks_by_album(tracks):
    counts = {}
    for t in tracks:
        name = t["album_name"]
        if name not in counts:
            counts[name] = 0
        if t["explicit"]:
            counts[name] += 1
    return counts


# Two-counter accumulator: [explicit_count, total_count], divide at the end.
# Same group-by skeleton as average_duration_by_album — a ratio is just a
# divide-at-the-end like an average. Kept separate from the raw count above
# because "how many" and "what fraction" answer different questions.
def explicit_ratio_by_album(tracks):
    counts = {}
    for t in tracks:
        name = t["album_name"]
        if name not in counts:
            counts[name] = [0, 0]
        counts[name][1] += 1
        if t["explicit"]:
            counts[name][0] += 1

    ratios = {}
    for name, (explicit_count, total_count) in counts.items():
        ratios[name] = explicit_count / total_count
    return ratios


def average_duration_by_album(tracks):
    totals = {}
    for t in tracks:
        name = t["album_name"]
        if name not in totals:
            totals[name] = [0, 0]
        totals[name][0] += t["duration_ms"]
        totals[name][1] += 1

    averages = {}
    for name, (sum_ms, count) in totals.items():
        averages[name] = sum_ms / count
    return averages


def releases_per_year(albums):
    counts = {}
    for album in albums:
        year = album["release_date"][:4]
        if year not in counts:
            counts[year] = 0
        counts[year] += 1
    return dict(sorted(counts.items()))


def gaps_between_albums(albums):
    ordered = sorted(albums, key=lambda a: a["release_date"])
    gaps = []
    for previous, current in zip(ordered, ordered[1:]):
        gap_years = int(current["release_date"][:4]) - int(previous["release_date"][:4])
        gaps.append({
            "from_album": previous["album_name"],
            "to_album": current["album_name"],
            "gap_years": gap_years,
        })
    return gaps


def track_length_trend(tracks):
    totals = {}
    for t in tracks:
        year = t["release_date"][:4]
        if year not in totals:
            totals[year] = [0, 0]
        totals[year][0] += t["duration_ms"]
        totals[year][1] += 1

    averages = {}
    for year, (sum_ms, count) in totals.items():
        averages[year] = sum_ms / count
    return dict(sorted(averages.items()))


def ms_to_min_sec(ms):
    total_seconds = ms // 1000
    hours = total_seconds // 3600
    remaining = total_seconds % 3600
    minutes = remaining // 60
    seconds = remaining % 60

    if hours > 0:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    return f"{minutes}:{seconds:02d}"


# ---------- Orchestrator ----------

def main(artist_name):
    os.makedirs("data/raw", exist_ok=True)
    os.makedirs("data/processed", exist_ok=True)

    token = get_access_token()

    artist_id = search_artist_id(artist_name, token)

    albums_raw = fetch_artist_albums(artist_id, token)
    save_json(albums_raw, "data/raw/artist_albums.json")

    all_albums = [normalize_album(a) for a in albums_raw]
    canonical_albums = dedup_albums(all_albums)

    all_tracks = []
    for album in canonical_albums:
        tracks_raw = fetch_album_tracks(album["album_id"], token)
        save_json(tracks_raw, f"data/raw/album_tracks_{album['album_id']}.json")
        all_tracks.extend(
            normalize_album_tracklist(
                tracks_raw, album["album_id"], album["album_name"], album["release_date"]
            )
        )

    write_csv(canonical_albums, "data/processed/albums.csv")
    write_csv(all_tracks, "data/processed/tracks.csv")

    biggest = album_with_most_tracks(canonical_albums)
    print(f"Album with most tracks: {biggest['album_name']} ({biggest['total_tracks']})")

    print("\nLongest tracks:")
    for t in longest_tracks(all_tracks, 5):
        print(f"  {t['name']} — {ms_to_min_sec(t['duration_ms'])} ({t['album_name']})")

    print("\nShortest tracks:")
    for t in shortest_tracks(all_tracks, 5):
        print(f"  {t['name']} — {ms_to_min_sec(t['duration_ms'])} ({t['album_name']})")

    # Categorical aggregates have no inherent order, so sort by value (biggest
    # first) for legibility. The two time-series below stay chronological.
    print("\nTotal runtime by album:")
    for name, total_ms in sorted(total_runtime_by_album(all_tracks).items(), key=lambda kv: kv[1], reverse=True):
        print(f"  {name}: {ms_to_min_sec(total_ms)}")

    print("\nExplicit tracks by album:")
    for name, count in sorted(explicit_tracks_by_album(all_tracks).items(), key=lambda kv: kv[1], reverse=True):
        print(f"  {name}: {count}")

    print("\nExplicit ratio by album:")
    for name, ratio in sorted(explicit_ratio_by_album(all_tracks).items(), key=lambda kv: kv[1], reverse=True):
        print(f"  {name}: {ratio:.0%}")

    print("\nAverage track duration by album:")
    for name, avg_ms in sorted(average_duration_by_album(all_tracks).items(), key=lambda kv: kv[1], reverse=True):
        print(f"  {name}: {ms_to_min_sec(int(avg_ms))}")

    print("\nReleases per year:")
    for year, count in releases_per_year(canonical_albums).items():
        print(f"  {year}: {count}")

    print("\nGaps between albums:")
    for gap in gaps_between_albums(canonical_albums):
        print(f"  {gap['from_album']} → {gap['to_album']}: {gap['gap_years']} yr")

    print("\nTrack length trend (avg per year):")
    for year, avg_ms in track_length_trend(all_tracks).items():
        print(f"  {year}: {ms_to_min_sec(int(avg_ms))}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch and analyze a Spotify artist's catalog")
    parser.add_argument("artist", help="Artist name to search for (e.g. \"Radiohead\")")
    args = parser.parse_args()
    main(args.artist)