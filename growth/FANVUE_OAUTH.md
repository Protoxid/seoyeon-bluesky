# FANVUE AUTH — OAUTH 2.0 + PKCE IS THE ONLY PATH
Corrected 5 Sep 2026. **This file previously recommended an API key. That was
wrong** and the correction is worth recording, because the mistake is a class of
mistake, not a typo.

## THE CONTRADICTION, AND WHICH SIDE WINS

Fanvue's **legal** API policy (https://legal.fanvue.com/api-policy, dated
5 Feb 2026) says, in these words:
> "All secured endpoints require the header `X-Fanvue-API-Key`."
> "Keys can be obtained and managed at https://www.fanvue.com/api-keys."
> "Only one active API key per user is permitted at any time."

Fanvue's **developer documentation** (https://api.fanvue.com/docs) says:
> "OAuth 2.0 with PKCE so your app can act on a creator's behalf, **with no
> static API keys**."
> "Create an app in the Fanvue Builder to get your OAuth Client ID and Secret,
> register your redirect URI, and pick the scopes your integration needs."

And a help article (4 Jun 2025) says API keys were never generally available:
> "Fanvue does not offer API keys for general use... When you request an API
> key, you are placed on a waiting list."

**`fanvue.com/api-keys` returns nothing. Shade checked.** The legal policy is
stale; the developer docs and the live site agree with each other.

**The rule this earns:** a legal or policy page describes what a company permits.
A developer doc describes what the software does. When they disagree about a
mechanism, the developer doc is the one that was written by the people who built
the endpoint — and the live site settles it. I trusted the policy page because it
was newer and more specific, and newer and more specific was still wrong.

---

## PREREQUISITE
> "A Fanvue creator account with KYC completed, only creators can access the
> Builder area. Fans cannot create or publish apps."

No KYC, no Builder, no credentials. Nothing below works first.

---

## STEP 1 — OPEN THE BUILDER
The docs call it the **Fanvue Builder**. The official starter repo
(github.com/fanvue/fanvue-app-starter) names the URL:

**https://fanvue.com/developers/apps**

If that path has also moved, look for **Developers / Builder / Apps** in the
creator settings. `auth.fanvue.com` is the login and consent server — it is not
where you register, and going there is a dead end.

## STEP 2 — CREATE AN APP
The form asks for a name, a **redirect URI**, and **scopes**.

## STEP 3 — REDIRECT URI
> "OAuth requires HTTPS redirect URIs, even in local development"

The docs contradict themselves here too: the quick-start shows
`https://my-fanvue-app.dev:3001/api/oauth/callback`, the starter README shows
`http://localhost:3000/api/oauth/callback`. Take the explicit HTTPS sentence as
governing.

**We already own an HTTPS domain and do not need to build a web app.**
`protoxiderpg.it` is live, behind Cloudflare, with SSL — set up for the
Instagram publishing pipeline. Register:

```
https://protoxiderpg.it/api/oauth/callback
```

It is static hosting, so nothing there processes the callback — and nothing
needs to. The authorisation code arrives as a query parameter in the browser's
address bar. Copy it out by hand once, exchange it locally for tokens, and
because `offline_access` returns a **refresh token**, that manual step happens
exactly once and never again.

That avoids Portless, mkcert, local-ssl-proxy, and running a Next.js app to
receive one string.

## STEP 4 — SCOPES
Full list, from https://api.fanvue.com/docs/authentication/scopes:

| resource | scopes |
|---|---|
| User | `read:self` |
| Chat | `read:chat`, `write:chat` |
| Fan | `read:fan` |
| Creator | `read:creator`, `write:creator` |
| Experience | `read:experience`, `write:experience` |
| Media | `read:media`, `write:media` |
| Posts | `read:post`, `write:post` |
| Insights | `read:insights` |
| Tracking Links | `read:tracking_links`, `write:tracking_links` |
| Agency | `read:agency`, `write:agency` |

**Select exactly these ten, and no more:**
```
read:self
read:chat   write:chat
read:fan
read:creator
read:media  write:media
read:post   write:post
read:insights
read:tracking_links  write:tracking_links
```
That covers everything in PLAN.md: `--whoami`, posting, welcome DMs, subscriber
reads, media upload, earnings, and tracking links.

**Do not select the Agency or Experience scopes.** We do not manage other
people's accounts, and a token that can is a token that can be misused.
> "Requests without sufficient scopes return a `403 Forbidden` error."

A 403 later is a two-minute fix. An over-scoped token is a standing liability.

> "OAUTH_SCOPES must exactly match the scopes selected in the Fanvue developer UI"

Set both sides in the same sitting. A mismatch fails at the authorise step with
an error that does not name the cause.

## STEP 5 — CLIENT ID AND SECRET
Both are generated on app creation. **Assume the secret is shown once.** Copy it
immediately into a gitignored file, `C:\AI-Project\growth\fanvue_oauth.env`:

```
OAUTH_CLIENT_ID=...
OAUTH_CLIENT_SECRET=...
OAUTH_SCOPES=read:self read:chat write:chat read:fan read:creator read:media write:media read:post write:post read:insights read:tracking_links write:tracking_links
OAUTH_REDIRECT_URI=https://protoxiderpg.it/api/oauth/callback
OAUTH_ISSUER_BASE_URL=https://auth.fanvue.com
API_BASE_URL=https://api.fanvue.com
```
The last two are fixed — do not change them.
Add `fanvue_oauth.env` and `fanvue_tokens.json` to `.gitignore` **before**
either file exists.

## STEP 6 — ONE AUTHORISATION, THEN NEVER AGAIN
`fanvue_auth.py` (Claude writes this) does:
1. generate a PKCE `code_verifier` and `code_challenge`
2. print the authorise URL — Shade opens it, logs in, approves
3. Shade copies the `code=...` value out of the address bar and pastes it back
4. exchange code + verifier for an access token and a **refresh token**
5. store tokens in `fanvue_tokens.json`, gitignored
6. every later run refreshes silently

Requests then carry `Authorization: Bearer <access_token>` and the pinned
`X-Fanvue-API-Version: YYYY-MM-DD`.

Rate limit is unchanged: **100 requests / 60 seconds**, with
`X-RateLimit-Limit`, `X-RateLimit-Remaining` and `X-RateLimit-Reset` on every
response and `429` when exceeded. Read those headers rather than guessing.

## SECURITY
- The client secret and the refresh token are both bearer credentials: whoever
  holds one is the account. Same handling as the Meta app secret.
- Never paste either into a chat, a prompt, a commit, a log or a report — not to
  Claude, not to Gemini. Scripts read them at runtime and never print them.
- Fanvue's policy bars sharing "client secrets, redirect URIs, or webhook
  callback URLs" with any third party, and bars creating an app "at the request,
  instruction, or encouragement of any third party". Shade creates it, in his own
  Builder, for his own account.

## STILL UNKNOWN
- Whether `read:fan` or `read:creator` is the one that returns the subscriber
  list — the scope docs do not map it. Both are in the set above, so the first
  call will settle it.
- Which scope governs **mass messages** — not stated. Probably `write:chat`.
  Untested, and mass messaging is not in scope this week anyway.
