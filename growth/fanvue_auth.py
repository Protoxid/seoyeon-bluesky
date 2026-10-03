#!/usr/bin/env python3
"""
fanvue_auth.py — one authorisation, then never again.

    python fanvue_auth.py --discover        what the server says its endpoints are
    python fanvue_auth.py --start           prints the URL to open in a browser
    python fanvue_auth.py --finish "<url>"  paste the FULL redirected URL back
    python fanvue_auth.py --status          are we authorised, and for how long
    python fanvue_auth.py --refresh         force a refresh now

WHY DISCOVERY INSTEAD OF HARDCODED PATHS. Fanvue's docs give the issuer
(auth.fanvue.com) but this file was written without a verified copy of their
authorize/token endpoint paths in hand. Guessing `/oauth/authorize` because that
is what most providers use is exactly the class of error that cost this project
a day on Kie -- a field name that belongs to a provider and a version, assumed
to transfer. OpenID Connect publishes a discovery document precisely so a client
never has to guess, so this reads it and uses what it finds. If Fanvue moves an
endpoint, this keeps working and nobody has to notice.

WHY THE REDIRECT GOES TO A STATIC SITE THAT CANNOT RECEIVE IT. Fanvue requires
an HTTPS redirect URI even locally. We already own protoxiderpg.it behind
Cloudflare with SSL, so it is registered as the redirect. Nothing there handles
the callback and nothing needs to: the authorisation code arrives as a query
parameter in the ADDRESS BAR. The page will show a 404. That is expected and is
not a failure -- the code is in the URL. Copy the whole URL, paste it into
--finish, and because the token response carries a refresh token, this happens
exactly once.

NOTHING IN THIS FILE EVER PRINTS A SECRET. Not the client secret, not a code,
not an access or refresh token. Lengths and expiry times only. A credential
printed to a terminal is a credential in the scrollback, and scrollback gets
pasted into chats.
"""
from __future__ import annotations
import argparse, base64, hashlib, json, os, pathlib, secrets, sys, time
import urllib.parse, urllib.request, urllib.error

ROOT = pathlib.Path(__file__).resolve().parent
ENV = ROOT / "fanvue_oauth.env"
TOKENS = ROOT / "fanvue_tokens.json"          # gitignored
PKCE = ROOT / "_pkce_state.json"              # short-lived, gitignored
OIDC = ROOT / "_oidc.json"                    # cached discovery, not secret

SECRET_KEYS = {"OAUTH_CLIENT_SECRET", "OAUTH_CLIENT_ID"}


def load_env() -> dict:
    env = {}
    if ENV.is_file():
        for ln in ENV.read_text(encoding="utf-8-sig").splitlines():
            ln = ln.strip()
            if not ln or ln.startswith("#") or "=" not in ln:
                continue
            k, v = ln.split("=", 1)
            env[k.strip()] = v.strip()

    # Fallback to environment variables (for GitHub Secrets / Cloud runners)
    for k in ("OAUTH_CLIENT_ID", "OAUTH_CLIENT_SECRET", "OAUTH_SCOPES",
              "OAUTH_REDIRECT_URI", "OAUTH_ISSUER_BASE_URL", "API_BASE_URL"):
        if not env.get(k) and os.environ.get(k):
            env[k] = os.environ[k].strip()

    for k in ("OAUTH_CLIENT_ID", "OAUTH_CLIENT_SECRET", "OAUTH_SCOPES",
              "OAUTH_REDIRECT_URI", "OAUTH_ISSUER_BASE_URL", "API_BASE_URL"):
        if not env.get(k) or env[k].startswith("PASTE"):
            sys.exit(f"  ! {k} is missing or still a placeholder in {ENV.name} / environment")
    return env


def http(url: str, data: bytes | None = None, headers: dict | None = None) -> dict:
    req = urllib.request.Request(url, data=data, headers=headers or {},
                                 method="POST" if data else "GET")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode()[:400]
        sys.exit(f"  ! HTTP {e.code} from {urllib.parse.urlparse(url).path}\n"
                 f"    {body}")
    except Exception as e:                                   # noqa: BLE001
        sys.exit(f"  ! {type(e).__name__}: {e}")


def discover(env: dict, refresh: bool = False) -> dict:
    if OIDC.is_file() and not refresh:
        return json.loads(OIDC.read_text())
    url = env["OAUTH_ISSUER_BASE_URL"].rstrip("/") + "/.well-known/openid-configuration"
    doc = http(url)
    for k in ("authorization_endpoint", "token_endpoint"):
        if k not in doc:
            sys.exit(f"  ! discovery document has no {k}\n"
                     f"    Fetched {url}\n"
                     f"    Report this — do not guess the path.")
    OIDC.write_text(json.dumps(doc, indent=2))
    return doc


def save_tokens(tok: dict) -> None:
    tok = dict(tok)
    tok["_obtained_at"] = int(time.time())
    TOKENS.write_text(json.dumps(tok, indent=2))
    try:
        os.chmod(TOKENS, 0o600)
    except Exception:                                        # noqa: BLE001
        pass          # Windows; the gitignore is the real guard here


def token() -> str:
    """Importable by every other script. Refreshes silently when stale."""
    # If running in cloud with FANVUE_TOKENS_JSON secret and file not on disk:
    if not TOKENS.is_file() and os.environ.get("FANVUE_TOKENS_JSON"):
        TOKENS.write_text(os.environ["FANVUE_TOKENS_JSON"].strip(), encoding="utf-8")

    env = load_env()
    if not TOKENS.is_file():
        sys.exit("  ! not authorised yet. Run: python fanvue_auth.py --start")
    t = json.loads(TOKENS.read_text())
    age = int(time.time()) - t.get("_obtained_at", 0)
    # 60s of slack: a token that expires mid-request is a 401 nobody expected.
    if age < int(t.get("expires_in", 3600)) - 60:
        return t["access_token"]
    if not t.get("refresh_token"):
        sys.exit("  ! access token expired and there is no refresh token.\n"
                 "    Re-run: python fanvue_auth.py --start")
    return refresh(env, t)["access_token"]


def refresh(env: dict, t: dict | None = None) -> dict:
    t = t or json.loads(TOKENS.read_text())
    doc = discover(env)
    creds = f"{env['OAUTH_CLIENT_ID']}:{env['OAUTH_CLIENT_SECRET']}".encode()
    auth_header = "Basic " + base64.b64encode(creds).decode()
    body = urllib.parse.urlencode({
        "grant_type": "refresh_token",
        "refresh_token": t["refresh_token"],
    }).encode()
    new = http(doc["token_endpoint"], body,
               {"Content-Type": "application/x-www-form-urlencoded",
                "Authorization": auth_header})
    # A refresh response may omit the refresh token, meaning "keep the old one".
    # Dropping it here would silently convert a permanent grant into a
    # one-hour one, and nobody would find out until the next morning.
    new.setdefault("refresh_token", t["refresh_token"])
    save_tokens(new)
    return new


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--discover", action="store_true")
    ap.add_argument("--start", action="store_true")
    ap.add_argument("--finish", metavar="URL")
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--refresh", action="store_true")
    a = ap.parse_args()
    env = load_env()

    if a.discover:
        doc = discover(env, refresh=True)
        print(f"  issuer      {doc.get('issuer')}")
        print(f"  authorize   {doc.get('authorization_endpoint')}")
        print(f"  token       {doc.get('token_endpoint')}")
        print(f"  pkce        {doc.get('code_challenge_methods_supported')}")
        print(f"  grants      {doc.get('grant_types_supported')}")
        sup = doc.get("scopes_supported")
        if sup:
            want = set(env["OAUTH_SCOPES"].split())
            missing = want - set(sup)
            print(f"  scopes      {len(sup)} advertised"
                  + (f"\n  ! NOT advertised by the server: {' '.join(sorted(missing))}"
                     if missing else "  (all ours are advertised)"))
        print(f"\n  cached to {OIDC.name}")
        return 0

    if a.start:
        doc = discover(env)
        verifier = base64.urlsafe_b64encode(secrets.token_bytes(64)).decode().rstrip("=")
        challenge = base64.urlsafe_b64encode(
            hashlib.sha256(verifier.encode()).digest()).decode().rstrip("=")
        state = secrets.token_urlsafe(24)
        PKCE.write_text(json.dumps({"verifier": verifier, "state": state,
                                    "at": int(time.time())}))
        q = urllib.parse.urlencode({
            "response_type": "code",
            "client_id": env["OAUTH_CLIENT_ID"],
            "redirect_uri": env["OAUTH_REDIRECT_URI"],
            "scope": env["OAUTH_SCOPES"],
            "state": state,
            "code_challenge": challenge,
            "code_challenge_method": "S256",
        })
        print("  1. Open this URL in the browser where you are logged in to Fanvue:\n")
        print(f"{doc['authorization_endpoint']}?{q}\n")
        print("  2. Approve. The browser lands on protoxiderpg.it and shows a")
        print("     404 or a blank page. THAT IS EXPECTED — the site is static")
        print("     and does not handle the callback. The code is in the URL.")
        print("  3. Copy the WHOLE address bar, then run:\n")
        print('     python fanvue_auth.py --finish "<paste the whole URL>"')
        return 0

    if a.finish:
        if not PKCE.is_file():
            sys.exit("  ! no pending authorisation. Run --start first.")
        st = json.loads(PKCE.read_text())
        qs = urllib.parse.parse_qs(urllib.parse.urlparse(a.finish).query)
        if "error" in qs:
            sys.exit(f"  ! the server returned an error: {qs['error'][0]}\n"
                     f"    {qs.get('error_description', [''])[0]}")
        code = (qs.get("code") or [None])[0]
        if not code:
            sys.exit("  ! no ?code= in that URL. Paste the FULL address bar,\n"
                     "    including everything after the question mark.")
        got_state = (qs.get("state") or [None])[0]
        if got_state != st["state"]:
            # Not paranoia: a mismatched state is the one signal that the code
            # in your clipboard belongs to a different authorisation than the
            # verifier on disk. Exchanging it would fail confusingly, or worse.
            sys.exit("  ! state mismatch — this URL is from a different --start.\n"
                     "    Run --start again and use its fresh URL.")
        doc = discover(env)
        creds = f"{env['OAUTH_CLIENT_ID']}:{env['OAUTH_CLIENT_SECRET']}".encode()
        auth_header = "Basic " + base64.b64encode(creds).decode()
        body = urllib.parse.urlencode({
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": env["OAUTH_REDIRECT_URI"],
            "code_verifier": st["verifier"],
        }).encode()
        tok = http(doc["token_endpoint"], body,
                   {"Content-Type": "application/x-www-form-urlencoded",
                    "Authorization": auth_header})
        if "access_token" not in tok:
            sys.exit(f"  ! no access_token in the response. Keys: {list(tok)}")
        save_tokens(tok)
        PKCE.unlink(missing_ok=True)
        print(f"  authorised.  access token {len(tok['access_token'])} chars, "
              f"expires in {tok.get('expires_in', '?')}s")
        if tok.get("refresh_token"):
            print("  refresh token stored — you will not have to do this again.")
        else:
            print("  ! NO refresh token was returned. This authorisation will")
            print("    expire and need repeating. Check that offline_access is")
            print("    enabled on the app before relying on unattended runs.")
        print(f"  saved to {TOKENS.name}  (gitignored, never printed)")
        return 0

    if a.refresh:
        t = refresh(env)
        print(f"  refreshed. expires in {t.get('expires_in','?')}s")
        return 0

    if a.status:
        if not TOKENS.is_file():
            print("  not authorised. Run: python fanvue_auth.py --start")
            return 1
        t = json.loads(TOKENS.read_text())
        left = int(t.get("expires_in", 0)) - (int(time.time()) - t.get("_obtained_at", 0))
        print(f"  access token   {len(t.get('access_token',''))} chars")
        print(f"  expires in     {left}s" + ("  (STALE — will refresh on next use)"
                                             if left <= 60 else ""))
        print(f"  refresh token  {'present' if t.get('refresh_token') else 'ABSENT'}")
        print(f"  granted scopes {t.get('scope','(not reported)')}")
        return 0

    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
