import requests
import pprint
import dotenv
import os


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

response = requests.get(
    "https://api.spotify.com/v1/search",
    headers={"Authorization": f"Bearer {access_token}"},
    params={"q": "The Beatles", "type": "artist"}
)

response_json = response.json()
if "error" in response_json:
    raise RuntimeError(f"Search API error: {response_json['error']}")

# drill down step by step
artists = response_json["artists"]
items = artists["items"]
first_artist = items[0]

# now pull out specific fields
print(first_artist["name"])
print(first_artist["id"])

# loop through all results
for artist in items:
    print(artist["name"])

