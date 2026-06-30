import requests
import dotenv
import os
import json
import csv

dotenv.load_dotenv()

client_id = os.getenv("SPOTIFY_CLIENT_ID")
client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")

if not client_id or not client_secret:
    raise RuntimeError("SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET must be set in .env")

# ---------- External world: auth + HTTP ----------

# Authenticate to get an access token
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


# Attaches the Bearer header, makes the GET, raises on any >= 400, returns JSON.
def spotify_get(path, access_token, params=None):
    response = requests.get(
        f"https://api.spotify.com/v1/{path}",
        headers={"Authorization": f"Bearer {access_token}"},
        params=params
    )
    if not response.ok:
        raise RuntimeError(f"Spotify API error: {response.text}")
    return response.json()

# ---------- External world: provider fetchers ----------

# Searches type=artist, takes the top hit's ID, raises if zero results.
def search_artist_id(name, token):
    response = spotify_get("search",token, {"q": f"artist:{name}", "type": "artist"})
    if not response["artists"]["items"]:
        raise RuntimeError(f"Artist not found: {name}")
    return response["artists"]["items"][0]["id"]  # returns id of first artist in array of ArtistObject

#raw album list - get albums from artist id
def fetch_artist_albums(artist_id, token):
    return spotify_get(f"artists/{artist_id}/albums", token, {"include_groups": "album", "limit": 5})  # only 5 "albums" for now

# raw track list - get tracks from an album
def fetch_album_tracks(album_id, token):
    return spotify_get(f"albums/{album_id}/tracks", token, {"limit": 5})  # only 5 tracks for now

# ---------- Normalization Layer----------
# One album -> one flat record.
def normalize_album(raw_album):
    return {
        "id": raw_album["id"],
        "album_name": raw_album["name"],
        "album_type": raw_album["album_type"],
        "total_tracks": raw_album["total_tracks"],
        "release_date": raw_album["release_date"],
    }


# One album's track list -> a list of flat track records.
# album_name and release_date are threaded in because SimplifiedTrackObject
# does not carry its own album reference.
def normalize_album_tracklist(raw_track_list, album_name, release_date):
    tracks = []
    for track in raw_track_list["items"]:
        tracks.append({
            "name": track["name"],
            "duration_ms": track["duration_ms"],
            "explicit": track["explicit"],
            "track_number": track["track_number"],
            "album_name": album_name,
            "release_date": release_date,
        })
    return tracks

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


def average_duration_by_album(tracks):
    totals = {}  # album_name -> [sum_ms, count]
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

def ms_to_min_sec(ms):
    seconds = ms // 1000
    return f"{seconds // 60}:{seconds % 60:02d}"


# ---------- Orchestrator ----------

def main():
    os.makedirs("data/raw", exist_ok=True)
    os.makedirs("data/processed", exist_ok=True)

    token = get_access_token()

    artist_name = "Taylor Swift"
    artist_id = search_artist_id(artist_name, token)

    albums_raw = fetch_artist_albums(artist_id, token)
    save_json(albums_raw, "data/raw/artist_albums.json")
    albums = [normalize_album(a) for a in albums_raw["items"]]
    all_tracks = []
    for album in albums:
        tracks_raw = fetch_album_tracks(album["id"], token)
        save_json(tracks_raw, f"data/raw/album_tracks_{album['id']}.json")
        all_tracks.extend(
            normalize_album_tracklist(
                tracks_raw, album["album_name"], album["release_date"]
            )
        )

    write_csv(all_tracks, "data/processed/tracks.csv")

    biggest = album_with_most_tracks(albums)
    print(f"Album with most tracks: {biggest['album_name']} ({biggest['total_tracks']})")

    print("\nLongest tracks:")
    for t in longest_tracks(all_tracks, 5):
        print(f"  {t['name']} — {ms_to_min_sec(t['duration_ms'])} ({t['album_name']})")

    print("\nAverage track duration by album:")
    for name, avg_ms in average_duration_by_album(all_tracks).items():
        print(f"  {name}: {ms_to_min_sec(int(avg_ms))}")

if __name__ == "__main__":
    main()


# access_token = get_access_token()
# response_json = response.json()
# if "error" in response_json:
#     raise RuntimeError(f"Search API error: {response_json['error']}")

# pprint.pprint(response_json)

# data = response.json()

#Probe the shape, one level at a time
# print("Top-level keys:", list(data.keys()))
# print("Number of items:", len(data["items"]))
# print("Keys of one item:", list(data["items"][0].keys()))
# print("Keys of item['track']:", list(data["items"][0]["track"].keys()))





