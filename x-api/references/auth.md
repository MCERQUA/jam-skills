# X API Authentication — Complete Reference

The X API supports four auth schemes. Pick the simplest that works.

| Method | Use for | Strength |
|---|---|---|
| **App-only Bearer** (OAuth 2.0 client credentials) | Public reads only, no user actions | Simplest |
| **OAuth 2.0 Authorization Code + PKCE** | User actions (post, like, DM, follow) | Modern, scoped |
| **OAuth 1.0a User Context** | Legacy / some media upload paths / Ads | Older, signature-based |
| **HTTP Basic** | Enterprise firehose/legacy | Enterprise-only |

## Prerequisites (all methods)

1. Create an **App** at https://developer.x.com — get: API Key, API Secret, Bearer Token, Client ID, Client Secret.
2. Configure **User authentication settings** on the app:
   - Type: **OAuth 2.0** (recommended) or OAuth 1.0a
   - **Callback URI** (must match exactly what you send in the auth URL)
   - App permissions: **Read**, **Read+Write**, or **Read+Write+Direct Messages** (required for DMs — scopes alone are not enough)
   - Website URL

## 1. App-only Bearer Token

**When to use:** public reads — post lookup, user lookup, recent search, trends, public timelines.
**Scopes:** not applicable — app-only auth has no scopes, access is determined by endpoint eligibility.

### Get a Bearer Token (once, then reuse)

The Developer Portal shows one; or generate via:

```bash
curl -u "$API_KEY:$API_SECRET" \
  --data 'grant_type=client_credentials' \
  'https://api.x.com/oauth2/token'
```

Response: `{"token_type":"bearer","access_token":"..."}`

### Use it

```bash
curl -H "Authorization: Bearer $BEARER" \
  'https://api.x.com/2/tweets/search/recent?query=claude%20code&max_results=10'
```

Python:

```python
import requests
r = requests.get(
    "https://api.x.com/2/tweets/search/recent",
    headers={"Authorization": f"Bearer {BEARER}"},
    params={"query": "claude code", "max_results": 10},
)
```

**Bearer tokens don't expire.** Store securely; rotate by revoking and regenerating.

## 2. OAuth 2.0 Authorization Code with PKCE (user context)

**When to use:** any user action — POST /2/tweets, likes, follows, DMs, bookmarks, `/users/me`.
**Token lifetime:** access_token 2 hours, refresh_token does not rotate by default (but confidential clients should rotate).

### Scope catalog

Request only what you need — shown on the user's consent screen.

| Scope | Enables |
|---|---|
| `tweet.read` | Read posts/timelines |
| `tweet.write` | Create & delete posts |
| `tweet.moderate.write` | Hide/unhide replies |
| `users.read` | Read user profiles (**required with any tweet scope**) |
| `follows.read` | List followers/following |
| `follows.write` | Follow/unfollow |
| `offline.access` | Return a refresh_token (**always request this**) |
| `like.read` | Read likes |
| `like.write` | Like/unlike |
| `list.read` | Read lists |
| `list.write` | Create/modify lists |
| `block.read` / `block.write` | Block mgmt |
| `mute.read` / `mute.write` | Mute mgmt |
| `space.read` | Read Spaces |
| `dm.read` / `dm.write` | DMs (app permission must also be DM-enabled) |
| `bookmark.read` / `bookmark.write` | Bookmarks |

### Flow (confidential client)

**Step 1 — Generate PKCE pair:**

```python
import secrets, hashlib, base64
code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).rstrip(b"=").decode()
code_challenge = base64.urlsafe_b64encode(
    hashlib.sha256(code_verifier.encode()).digest()
).rstrip(b"=").decode()
```

**Step 2 — Redirect user to authorize:**

```
https://x.com/i/oauth2/authorize?
  response_type=code
  &client_id=CLIENT_ID
  &redirect_uri=https%3A%2F%2Fyourapp.com%2Fcallback
  &scope=tweet.read%20tweet.write%20users.read%20offline.access
  &state=CSRF_RANDOM
  &code_challenge=CODE_CHALLENGE
  &code_challenge_method=S256
```

**Step 3 — User approves → X redirects to your callback with `code` and `state`.** Verify `state` matches.

**Step 4 — Exchange code for tokens:**

```bash
curl -u "$CLIENT_ID:$CLIENT_SECRET" \
  -X POST https://api.x.com/2/oauth2/token \
  -d "grant_type=authorization_code" \
  -d "code=$CODE" \
  -d "redirect_uri=$REDIRECT_URI" \
  -d "code_verifier=$CODE_VERIFIER"
```

Response:

```json
{
  "token_type": "bearer",
  "expires_in": 7200,
  "access_token": "...",
  "refresh_token": "...",
  "scope": "tweet.read tweet.write users.read offline.access"
}
```

**Step 5 — Call user-context endpoints:**

```bash
curl -H "Authorization: Bearer $USER_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -X POST https://api.x.com/2/tweets \
  -d '{"text":"hello from the X API"}'
```

**Step 6 — Refresh before expiry (every ~2 hours):**

```bash
curl -u "$CLIENT_ID:$CLIENT_SECRET" \
  -X POST https://api.x.com/2/oauth2/token \
  -d "grant_type=refresh_token" \
  -d "refresh_token=$REFRESH_TOKEN"
```

Response includes new `access_token` and a new `refresh_token` (use the latest — old one stays valid briefly for race-safety).

### Public client (mobile/SPA, no secret)

Same flow, but:
- Don't use `-u CLIENT_ID:CLIENT_SECRET` — instead send `client_id` in the body.
- PKCE becomes the only proof (this is the point of PKCE).

### Python (end-to-end minimal OAuth 2.0 user flow)

```python
import os, secrets, hashlib, base64, urllib.parse, requests, webbrowser, http.server

CLIENT_ID     = os.environ["X_CLIENT_ID"]
CLIENT_SECRET = os.environ["X_CLIENT_SECRET"]  # optional (public client)
REDIRECT      = "http://127.0.0.1:5055/cb"
SCOPES = "tweet.read tweet.write users.read offline.access"

verifier  = base64.urlsafe_b64encode(secrets.token_bytes(32)).rstrip(b"=").decode()
challenge = base64.urlsafe_b64encode(
    hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
state     = secrets.token_urlsafe(16)

auth_url = "https://x.com/i/oauth2/authorize?" + urllib.parse.urlencode({
    "response_type": "code",
    "client_id": CLIENT_ID,
    "redirect_uri": REDIRECT,
    "scope": SCOPES,
    "state": state,
    "code_challenge": challenge,
    "code_challenge_method": "S256",
})
print("Open:", auth_url)
webbrowser.open(auth_url)

# Mini callback receiver
code_holder = {}
class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        qs = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        code_holder["code"] = qs.get("code", [None])[0]
        code_holder["state"] = qs.get("state", [None])[0]
        self.send_response(200); self.end_headers()
        self.wfile.write(b"ok, close window")
http.server.HTTPServer(("127.0.0.1", 5055), H).handle_request()

assert code_holder["state"] == state, "CSRF mismatch"

auth = (CLIENT_ID, CLIENT_SECRET) if CLIENT_SECRET else None
tok = requests.post(
    "https://api.x.com/2/oauth2/token",
    auth=auth,
    data={
        "grant_type": "authorization_code",
        "code": code_holder["code"],
        "redirect_uri": REDIRECT,
        "code_verifier": verifier,
        **({"client_id": CLIENT_ID} if not CLIENT_SECRET else {}),
    },
).json()
print(tok)
```

## 3. OAuth 1.0a User Context

**When to use:**
- Legacy endpoints that haven't been re-exposed on v2
- Media uploads with OAuth 1.0a (still widely used though v2 OAuth 2.0 also supports media now)
- Ads API
- When your library (tweepy, twitter-api-v2) defaults to 1.0a

### Credentials

- **Consumer Key / Consumer Secret** — your app
- **Access Token / Access Token Secret** — per user (your own in dev portal; 3-legged flow for others)

### Signing (use a library — don't roll your own)

```python
# Python: requests_oauthlib
from requests_oauthlib import OAuth1
auth = OAuth1(CK, CS, AT, ATS)
requests.post("https://api.x.com/2/tweets",
              auth=auth, json={"text": "hi"})
```

```python
# Python: tweepy v4+
import tweepy
client = tweepy.Client(
    consumer_key=CK, consumer_secret=CS,
    access_token=AT, access_token_secret=ATS,
)
client.create_tweet(text="hi")
```

### 3-legged flow (for other users' accounts)

1. `POST /oauth/request_token` with `oauth_callback` → get `oauth_token` + `oauth_token_secret`
2. Redirect user to `https://api.x.com/oauth/authorize?oauth_token=...`
3. User approves → X redirects to callback with `oauth_token` + `oauth_verifier`
4. `POST /oauth/access_token` with the verifier → permanent access token + secret
5. Store per-user, sign all their requests with `(CK, CS, AT_u, ATS_u)`

## 4. HTTP Basic (Enterprise)

Some legacy enterprise endpoints (Gnip firehose, older compliance) accept `Authorization: Basic base64(user:pass)` with credentials provisioned by your account manager. Use TLS always.

## Choosing — decision tree

```
Are you only reading public data?
├─ yes → App-only Bearer
└─ no  → Are you acting on behalf of a user?
         ├─ yes → Is this new code? ─── yes → OAuth 2.0 PKCE
         │                              └── no  → OAuth 1.0a (if library already uses it)
         └─ Enterprise firehose? → HTTP Basic
```

## Security checklist

- [ ] Client secret NEVER in frontend code; use a backend or PKCE-only public client.
- [ ] Tokens in env or secret manager; never in git.
- [ ] Rotate Bearer on leak (revoke in portal).
- [ ] Validate `state` on OAuth 2.0 callback.
- [ ] Store PKCE `code_verifier` server-side between redirect and callback.
- [ ] Refresh OAuth 2.0 tokens server-side; on refresh failure, force re-auth (don't loop).
- [ ] Short TTL on cached tokens; fail open to re-auth rather than stale-token errors.
- [ ] For DMs: confirm the app's **permission toggle** is "Read and write and Direct message" (scopes alone don't authorize the token).

## Common 401/403 causes

| Symptom | Cause |
|---|---|
| `401 Unauthorized` on first POST /2/tweets | App permission set to Read-only; change to Read+Write, **regenerate token**, re-auth user. |
| `403 client-not-enrolled` | Your project/app isn't attached to an access tier. Sign up for pay-per-use in Console. |
| `403 Forbidden` on `/search/all` | Requires Pro+. |
| `401` on OAuth 1.0a | Clock drift >5 min, or nonce reused. Use a fresh nonce per call. |
| DM send returns 403 | App permission wasn't set to include DM when token was issued. Re-issue token. |
