#!/usr/bin/env python3
"""
One-time OAuth 1.0a PIN flow to get X/Twitter user Access Token + Secret.
Run this once to authorize @metx_mike, then the tokens are saved to .platform-keys.env.

Usage:
  source /mnt/system/base/.platform-keys.env
  python3 /mnt/system/base/skills/x-bookmarks/x-auth-setup.py
"""
import os, sys, requests
from requests_oauthlib import OAuth1

API_KEY    = os.environ.get("X_API_KEY")
API_SECRET = os.environ.get("X_API_SECRET")

if not API_KEY or not API_SECRET:
    print("ERROR: X_API_KEY and X_API_SECRET must be set")
    sys.exit(1)

# Step 1: get a request token (callback=oob = PIN mode, no redirect URL needed)
r = requests.post(
    "https://api.twitter.com/oauth/request_token",
    auth=OAuth1(API_KEY, API_SECRET),
    params={"oauth_callback": "oob"},
)
if r.status_code != 200:
    print(f"ERROR getting request token: {r.status_code} {r.text}")
    sys.exit(1)

params = dict(pair.split("=") for pair in r.text.split("&"))
request_token = params["oauth_token"]

# Step 2: print auth URL for Mike to open
print()
print("=" * 60)
print("STEP 1 — Open this URL in your browser and authorize the app:")
print()
print(f"  https://api.twitter.com/oauth/authorize?oauth_token={request_token}")
print()
print("STEP 2 — After authorizing, X will show you a PIN number.")
print("=" * 60)
print()

pin = input("Enter the PIN from X: ").strip()

# Step 3: exchange PIN for access token
r = requests.post(
    "https://api.twitter.com/oauth/access_token",
    auth=OAuth1(API_KEY, API_SECRET, request_token),
    params={"oauth_verifier": pin},
)
if r.status_code != 200:
    print(f"ERROR exchanging PIN: {r.status_code} {r.text}")
    sys.exit(1)

result = dict(pair.split("=") for pair in r.text.split("&"))
access_token        = result["oauth_token"]
access_token_secret = result["oauth_token_secret"]
screen_name         = result.get("screen_name", "unknown")

print()
print(f"SUCCESS — authorized as @{screen_name}")
print()
print("Saving to /mnt/system/base/.platform-keys.env ...")

env_path = "/mnt/system/base/.platform-keys.env"
with open(env_path, "r") as f:
    content = f.read()

# Update or insert X_ACCESS_TOKEN
for var, val in [("X_ACCESS_TOKEN", access_token), ("X_ACCESS_TOKEN_SECRET", access_token_secret)]:
    if f"{var}=" in content:
        lines = content.splitlines()
        new_lines = []
        for line in lines:
            if line.startswith(f"{var}="):
                new_lines.append(f"{var}={val}")
            else:
                new_lines.append(line)
        content = "\n".join(new_lines) + "\n"
    else:
        content += f"{var}={val}\n"

with open(env_path, "w") as f:
    f.write(content)

print(f"  X_ACCESS_TOKEN        = {access_token}")
print(f"  X_ACCESS_TOKEN_SECRET = {access_token_secret}")
print()
print("Done. Test with:")
print("  source /mnt/system/base/.platform-keys.env && bash /mnt/system/base/skills/x-bookmarks/fetch-bookmarks.sh 5")
