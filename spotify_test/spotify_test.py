import requests
import dotenv
import os
import json
import csv
import time

dotenv.load_dotenv()

client_id = os.getenv("SPOTIFY_CLIENT_ID")
client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")

if not client_id or not client_secret:
    raise RuntimeError("SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET must be set in .env")

# ---------- External world: auth + HTTP ----------

def get_access_token():
    response = requests.post(
        "https://accounts.spotify.com/api/token",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret
        }
    )
    if not response.ok:
        raise RuntimeError(f"Failed to get access token: {response.text}")
    return response.json()["access_token"]


# Attaches the Bearer header, makes the GET, retries once on 429 using
# Spotify's Retry-After header, raises on any other >= 400, returns JSON.
def spotify_get(path, access_token, params=None):
    url = f"https://api.spotify.com/v1/{path}"
    headers = {"Authorization": f"Bearer {access_token}"}

    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 429:
        wait_seconds = int(response.headers.get("Retry-After", 1))
        time.sleep(wait_seconds)
        response = requests.get(url, headers=headers, params=params)

    if not response.ok:
        raise RuntimeError(f"Spotify API error: {response.text}")
    return response.json()


# Generic pagination helper — walks offset forward until a page comes back
# empty. Does NOT trust "next" or "total" as the stop signal (Spotify has a
# known bug where "next" keeps pointing forward past the real end), so an
# empty items page is the only thing that ends the loop. max_pages is a
# fail-fast backstop in case that bug (or something else) causes a runaway.
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


# Returns a FLAT LIST of every raw album across all pages (pagination is
# hidden inside paginate — callers never see offset/limit mechanics).
def fetch_artist_albums(artist_id, token):
    return paginate(f"artists/{artist_id}/albums", token, {"include_groups": "album", "limit": 10})


# Returns a FLAT LIST of every raw track across all pages, same reasoning.
def fetch_album_tracks(album_id, token):
    return paginate(f"albums/{album_id}/tracks", token, {"limit": 50})


# ---------- Normalization Layer ----------

def normalize_album(raw_album):
    return {
        "id": raw_album["id"],
        "album_name": raw_album["name"],
        "album_type": raw_album["album_type"],
        "total_tracks": raw_album["total_tracks"],
        "release_date": raw_album["release_date"],
    }


# raw_track_list is now a flat list (paginate already unwrapped "items"),
# so this iterates directly instead of indexing ["items"].
def normalize_album_tracklist(raw_track_list, album_name, release_date):
    tracks = []
    for track in raw_track_list:
        tracks.append({
            "name": track["name"],
            "duration_ms": track["duration_ms"],
            "explicit": track["explicit"],
            "track_number": track["track_number"],
            "album_name": album_name,
            "release_date": release_date,
        })
    return tracks


# ---------- Deduplication ----------

# Strips a trailing "(...)" or "[...]" edition marker off an album name,
# e.g. "1989 (Deluxe)" -> "1989". Used only as a comparison key — the
# original name is kept for display/output.
def canonical_title(album_name):
    cut_at = len(album_name)
    for bracket in ["(", "["]:
        idx = album_name.find(bracket)
        if idx != -1:
            cut_at = min(cut_at, idx)
    return album_name[:cut_at].strip().lower()


# Groups album editions by canonical_title, then keeps exactly one
# representative per group: the earliest release_date, and — if two
# editions share a release date (this really happens: TTPD and TTPD:
# THE ANTHOLOGY both list "2024-04-19") — the one with fewer total_tracks,
# since the smaller one is the standard edition and the larger one is the
# expanded/deluxe repackage.
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


# Handles durations past 60 minutes (e.g. total album runtime) by adding
# an hour place only when needed, so a 3-minute track still prints "3:45"
# instead of "0:03:45".
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

def main():
    os.makedirs("data/raw", exist_ok=True)
    os.makedirs("data/processed", exist_ok=True)

    token = get_access_token()

    artist_name = "As I Lay Dying"
    artist_id = search_artist_id(artist_name, token)

    albums_raw = fetch_artist_albums(artist_id, token)
    save_json(albums_raw, "data/raw/artist_albums.json")

    all_albums = [normalize_album(a) for a in albums_raw]
    canonical_albums = dedup_albums(all_albums)

    all_tracks = []
    for album in canonical_albums:
        tracks_raw = fetch_album_tracks(album["id"], token)
        save_json(tracks_raw, f"data/raw/album_tracks_{album['id']}.json")
        all_tracks.extend(
            normalize_album_tracklist(tracks_raw, album["album_name"], album["release_date"])
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

    print("\nTotal runtime by album:")
    for name, total_ms in total_runtime_by_album(all_tracks).items():
        print(f"  {name}: {ms_to_min_sec(total_ms)}")

    print("\nExplicit tracks by album:")
    for name, count in explicit_tracks_by_album(all_tracks).items():
        print(f"  {name}: {count}")

    print("\nAverage track duration by album:")
    for name, avg_ms in average_duration_by_album(all_tracks).items():
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
    main()