"""The single Spotify seam: OAuth Authorization Code flow + the spotify_get gateway.

Invariant 2: one auth path - Authorization Code with a loopback-literal
redirect. Client Credentials is dead. Refresh failure THROWS; no retry
loops around auth.
Invariant 3: every Spotify Web API call goes through spotify_get - network
retry and 429 Retry-After handling live here and only here.

One-time interactive authorization:  .venv/bin/python -m src.common.spotify
Endpoint mechanics per API_NOTES.md (verified 2026-07-12/15).
"""

import base64
import http.server
import json
import os
import secrets
import sys
import time
import urllib.parse
import webbrowser
from pathlib import Path

import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")

TOKENS_PATH = ROOT / "secrets" / "tokens.json"
REDIRECT_PORT = 8888
REDIRECT_URI = f"http://127.0.0.1:{REDIRECT_PORT}/callback"  # loopback literal, never localhost
SCOPE = "user-read-recently-played"
AUTHORIZE_URL = "https://accounts.spotify.com/authorize"
TOKEN_URL = "https://accounts.spotify.com/api/token"
API_BASE = "https://api.spotify.com/v1"
REQUEST_TIMEOUT = 10  # seconds; a hung connection can never fail fast
EXPIRY_MARGIN_SECONDS = 60  # refresh slightly early so a token never expires mid-request


def _client_credentials():
    client_id = os.getenv("SPOTIFY_CLIENT_ID")
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
    if not client_id or not client_secret:
        raise RuntimeError("SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET must be set in .env")
    return client_id, client_secret


def _basic_auth_header(client_id, client_secret):
    encoded = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    return {"Authorization": f"Basic {encoded}"}


# ---------- One-time interactive authorization ----------

def run_auth_flow():
    client_id, client_secret = _client_credentials()
    state = secrets.token_hex(16)
    authorize_url = AUTHORIZE_URL + "?" + urllib.parse.urlencode({
        "client_id": client_id,
        "response_type": "code",
        "redirect_uri": REDIRECT_URI,
        "scope": SCOPE,
        "state": state,
    })
    code = _catch_callback(authorize_url, state)
    tokens = _exchange_code(code, client_id, client_secret)
    _write_tokens(tokens)
    print(f"Authorized. Tokens written to {TOKENS_PATH} (mode 600).")


def _catch_callback(authorize_url, expected_state):
    """Serve exactly one request on the loopback port and return the auth code."""
    result = {}

    class CallbackHandler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            result["query"] = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"Authorization received - you can close this tab.")

        def log_message(self, *args):
            pass  # default per-request logging is noise here

    server = http.server.HTTPServer(("127.0.0.1", REDIRECT_PORT), CallbackHandler)
    print(f"Opening browser; waiting for Spotify callback on {REDIRECT_URI} ...")
    webbrowser.open(authorize_url)
    server.handle_request()  # one-shot: handle the callback, then stop
    server.server_close()

    query = result.get("query", {})
    if "error" in query:
        raise RuntimeError(f"Spotify authorization denied: {query['error'][0]}")
    if query.get("state", [None])[0] != expected_state:
        raise RuntimeError("OAuth state mismatch - possible CSRF; aborting")
    if "code" not in query:
        raise RuntimeError(f"Callback carried no auth code (query keys: {sorted(query)})")
    return query["code"][0]


def _exchange_code(code, client_id, client_secret):
    response = requests.post(
        TOKEN_URL,
        headers=_basic_auth_header(client_id, client_secret),
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": REDIRECT_URI,  # validation only, no redirection happens
        },
        timeout=REQUEST_TIMEOUT,
    )
    if not response.ok:
        # failure bodies carry error codes only, never tokens - safe to surface
        raise RuntimeError(f"Token exchange failed: HTTP {response.status_code} {response.text}")
    payload = response.json()
    return {
        "access_token": payload["access_token"],
        "refresh_token": payload["refresh_token"],
        "scope": payload["scope"],
        "expires_in": payload["expires_in"],
        "issued_at": int(time.time()),  # expiry is computed locally from this
    }


def _write_tokens(tokens):
    # 0o600 at creation - the file is never world-readable, not even briefly
    fd = os.open(TOKENS_PATH, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as f:
        json.dump(tokens, f, indent=2)


# ---------- Token access for jobs ----------

def get_valid_access_token():
    if not TOKENS_PATH.exists():
        raise RuntimeError(
            f"{TOKENS_PATH} not found - run `.venv/bin/python -m src.common.spotify` to authorize"
        )
    with open(TOKENS_PATH) as f:
        tokens = json.load(f)
    expires_at = tokens["issued_at"] + tokens["expires_in"] - EXPIRY_MARGIN_SECONDS
    if time.time() >= expires_at:
        tokens = _refresh(tokens)
        _write_tokens(tokens)
        print("token refreshed", file=sys.stderr)
    return tokens["access_token"]


def _refresh(tokens):
    client_id, client_secret = _client_credentials()
    response = requests.post(
        TOKEN_URL,
        headers=_basic_auth_header(client_id, client_secret),
        data={"grant_type": "refresh_token", "refresh_token": tokens["refresh_token"]},
        timeout=REQUEST_TIMEOUT,
    )
    if not response.ok:
        raise RuntimeError(
            f"Token refresh failed (HTTP {response.status_code}) - "
            "re-run `.venv/bin/python -m src.common.spotify` to re-authorize"
        )
    payload = response.json()
    return {
        "access_token": payload["access_token"],
        # refresh responses MAY omit refresh_token - keep the current one (API_NOTES 2026-07-12)
        "refresh_token": payload.get("refresh_token", tokens["refresh_token"]),
        "scope": payload.get("scope", tokens["scope"]),
        "expires_in": payload["expires_in"],
        "issued_at": int(time.time()),
    }


# ---------- The gateway ----------

def spotify_get(path, params=None):
    url = f"{API_BASE}/{path}"
    headers = {"Authorization": f"Bearer {get_valid_access_token()}"}

    try:
        response = requests.get(url, headers=headers, params=params, timeout=REQUEST_TIMEOUT)
    except requests.exceptions.RequestException as e:
        # exception TYPE and path only - never headers (Bearer token)
        print(f"Network error on {path} ({type(e).__name__}), retrying once", file=sys.stderr)
        time.sleep(2)
        response = requests.get(url, headers=headers, params=params, timeout=REQUEST_TIMEOUT)

    if response.status_code == 429:
        wait_seconds = int(response.headers.get("Retry-After", 1))
        time.sleep(wait_seconds)
        response = requests.get(url, headers=headers, params=params, timeout=REQUEST_TIMEOUT)

    if not response.ok:
        raise RuntimeError(f"Spotify API error on {path}: HTTP {response.status_code} {response.text}")
    return response.json()


if __name__ == "__main__":
    run_auth_flow()
    items = spotify_get("me/player/recently-played", {"limit": 1})["items"]
    print(f"Smoke test: recently-played returned {len(items)} item(s) - scope granted, gateway working.")
