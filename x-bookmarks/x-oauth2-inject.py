#!/usr/bin/env python3
"""
Injects OAuth 2.0 PKCE routes into the running openvoiceui-mike container.
Adds:
  GET  /x-oauth/start    — redirects browser to X auth page
  GET  /x-oauth/callback — captures code, exchanges for tokens, saves them

Usage (run once from host):
  python3 /mnt/system/base/skills/x-bookmarks/x-oauth2-inject.py
"""

ROUTE_CODE = '''
import secrets, hashlib, base64, json as _json, os as _os
import requests as _requests

_X_STATE_STORE = {}

@app.route("/x-oauth/start")
def x_oauth_start():
    client_id = _os.environ.get("X_CLIENT_ID", "")
    if not client_id:
        return "X_CLIENT_ID not set", 500

    code_verifier  = secrets.token_urlsafe(64)
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode()).digest()
    ).rstrip(b"=").decode()
    state = secrets.token_hex(16)
    _X_STATE_STORE[state] = code_verifier

    params = {
        "response_type":         "code",
        "client_id":             client_id,
        "redirect_uri":          "https://mike.jam-bot.com/x-oauth/callback",
        "scope":                 "tweet.read users.read bookmark.read bookmark.write offline.access",
        "state":                 state,
        "code_challenge":        code_challenge,
        "code_challenge_method": "S256",
    }
    from urllib.parse import urlencode
    url = "https://twitter.com/i/oauth2/authorize?" + urlencode(params)
    from flask import redirect as _redirect
    return _redirect(url)

@app.route("/x-oauth/callback")
def x_oauth_callback():
    from flask import request as _req
    code  = _req.args.get("code")
    state = _req.args.get("state")
    error = _req.args.get("error")

    if error:
        return f"Auth error: {error}", 400
    if not code or state not in _X_STATE_STORE:
        return "Invalid state", 400

    code_verifier = _X_STATE_STORE.pop(state)
    client_id     = _os.environ.get("X_CLIENT_ID", "")
    client_secret = _os.environ.get("X_CLIENT_SECRET", "")

    data = {
        "grant_type":    "authorization_code",
        "code":          code,
        "redirect_uri":  "https://mike.jam-bot.com/x-oauth/callback",
        "code_verifier": code_verifier,
    }
    if client_secret:
        r = _requests.post("https://api.twitter.com/2/oauth2/token",
                           data=data,
                           auth=(client_id, client_secret))
    else:
        data["client_id"] = client_id
        r = _requests.post("https://api.twitter.com/2/oauth2/token", data=data)

    if r.status_code != 200:
        return f"Token exchange failed: {r.text}", 500

    tokens = r.json()
    access_token  = tokens.get("access_token", "")
    refresh_token = tokens.get("refresh_token", "")

    # Save to platform-keys.env on the HOST via mounted path
    env_path = "/mnt/platform-keys.env"
    try:
        with open(env_path, "r") as f:
            content = f.read()
        for var, val in [("X_OAUTH2_ACCESS_TOKEN", access_token),
                         ("X_OAUTH2_REFRESH_TOKEN", refresh_token)]:
            if f"{var}=" in content:
                lines = content.splitlines()
                content = "\\n".join(
                    (f"{var}={val}" if l.startswith(f"{var}=") else l)
                    for l in lines
                ) + "\\n"
            else:
                content += f"{var}={val}\\n"
        with open(env_path, "w") as f:
            f.write(content)
        saved = "Saved to platform-keys.env"
    except Exception as e:
        saved = f"WARNING: could not save to file: {e}. Tokens below."

    return f"""<h2>X Auth Complete</h2>
<p>{saved}</p>
<pre>X_OAUTH2_ACCESS_TOKEN={access_token}
X_OAUTH2_REFRESH_TOKEN={refresh_token}</pre>
<p>Copy these if the file save failed, then close this page.</p>"""
'''

import subprocess, sys

inject_cmd = f"""
python3 -c "
import sys
code = '''{ROUTE_CODE}'''
with open('/app/server.py', 'r') as f:
    content = f.read()
if '/x-oauth/start' in content:
    print('Routes already injected')
    sys.exit(0)
# Append before the last line
with open('/app/server.py', 'a') as f:
    f.write(code)
print('Injected OK')
"
"""

result = subprocess.run(
    ["sg", "docker", "-c",
     f"docker exec openvoiceui-mike bash -c {repr(inject_cmd.strip())}"],
    capture_output=True, text=True
)
print(result.stdout or result.stderr)
