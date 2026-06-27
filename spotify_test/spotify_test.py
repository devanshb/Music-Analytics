import requests
import pprint
import dotenv
import os
import json


dotenv.load_dotenv()

client_id = os.getenv("SPOTIFY_CLIENT_ID")
client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")

if not client_id or not client_secret:
    raise RuntimeError("SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET must be set in .env")

response = requests.post(
    "https://accounts.spotify.com/api/token",
    headers={"Content-Type": "application/x-www-form-urlencoded"},
    data={
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret
    }
)

token_data = response.json()
access_token = token_data.get("access_token")
if not access_token:
    raise RuntimeError(f"Failed to get access token: {token_data}")

playlist_id = "1ZJpJahEFst7u8njXeGFyv"

response = requests.get(
    f"https://api.spotify.com/v1/playlists/{playlist_id}/items",
    headers={"Authorization": f"Bearer {access_token}"},
    #params={"limit":5}
)

response_json = response.json()
if "error" in response_json:
    raise RuntimeError(f"Search API error: {response_json['error']}")

pprint.pprint(response_json)

data = response.json()

#Probe the shape, one level at a time
print("Top-level keys:", list(data.keys()))
print("Number of items:", len(data["items"]))
print("Keys of one item:", list(data["items"][0].keys()))
print("Keys of item['track']:", list(data["items"][0]["track"].keys()))





