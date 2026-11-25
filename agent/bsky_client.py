"""
agent/bsky_client.py — AT Protocol & Bluesky XRPC Client for Seo-yeon.

Features:
  - Session authentication & token management.
  - Timeline & feed browsing (timeline, search, thread reconstruction).
  - Notifications polling (mentions, replies, quotes, likes).
  - Direct Messages via chat.bsky.convo.* with proxy header (atproto-proxy: did:web:api.bsky.chat#bsky_chat).
  - Rich text facet generation for hashtags (#tag).
  - Post creation (text-only, images via uploadBlob, replies, likes).
  - Complete DRY_RUN simulation support.
"""

from __future__ import annotations

import datetime as dt
import io
import json
import re
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional, Set, Tuple

from PIL import Image

from .config import config


class BlueskyClient:
    def __init__(
        self,
        handle: Optional[str] = None,
        app_password: Optional[str] = None,
        dry_run: Optional[bool] = None,
    ):
        self.handle = handle or config.bsky_handle
        self.app_password = app_password or config.bsky_app_password
        self.dry_run = dry_run if dry_run is not None else config.dry_run

        if self.handle and "." not in self.handle:
            self.handle = f"{self.handle}.bsky.social"

        self.jwt: Optional[str] = None
        self.did: Optional[str] = None
        self.dm_available: bool = True  # Track if app password has DM permission
        self._did_cache: Dict[str, Optional[str]] = {}
        self._saved_feed_uris: Optional[List[str]] = None

    def authenticate(self) -> bool:
        """Establishes an AT Protocol session."""
        if not self.handle or not self.app_password:
            return False

        url = f"{config.bsky_xrpc_base}/com.atproto.server.createSession"
        data = json.dumps({"identifier": self.handle, "password": self.app_password}).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                res = json.loads(resp.read().decode("utf-8"))
                self.jwt = res.get("accessJwt")
                self.did = res.get("did")
                return True
        except Exception as e:
            print(f"[BlueskyClient] Authentication failed: {e}")
            return False

    def ensure_session(self) -> bool:
        if self.dry_run:
            if not self.did:
                self.did = "did:plc:simulated"
            return True
        if not self.jwt or not self.did:
            return self.authenticate()
        return True

    # --- XRPC Helpers ---
    def xrpc_get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if not self.ensure_session():
            return {}
        qs = urllib.parse.urlencode(params or {})
        url = f"{config.bsky_xrpc_base}/{endpoint}"
        if qs:
            url = f"{url}?{qs}"
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {self.jwt}"})
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            print(f"[BlueskyClient XRPC GET] {endpoint} error: {e}")
            return {}

    def xrpc_post(self, endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        from .runtime import may_publish
        if self.dry_run or not may_publish():
            return {"simulated": True}
        if endpoint == "com.atproto.repo.createRecord":
            from .delivery import Outbox, action_key, new_record_key
            record = payload.get("record", {})
            subject = record.get("subject", {})
            identity = (getattr(self, "action_identity", "") or json.dumps(record, sort_keys=True))
            if payload.get("collection") in {"app.bsky.feed.like", "app.bsky.feed.repost", "app.bsky.graph.follow"}:
                identity = json.dumps(subject, sort_keys=True)
            key = action_key(payload.get("collection", endpoint), identity)
            # Internal deduplication hashes are not valid Bluesky TIDs. The
            # outbox preserves the first timestamp key across retries/restarts.
            payload = dict(payload, rkey=payload.get("rkey") or new_record_key())
            def lookup(saved):
                found = self.xrpc_get("com.atproto.repo.getRecord", {k:saved[k] for k in ("repo", "collection", "rkey")})
                return found if found.get("uri") else None
            return Outbox().send(key, endpoint, payload, self._xrpc_post_raw, lookup, idempotent=True)
        return self._xrpc_post_raw(endpoint, payload)

    def _xrpc_post_raw(self, endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        if not self.ensure_session():
            return {}
        url = f"{config.bsky_xrpc_base}/{endpoint}"
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {self.jwt}"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                raw = resp.read().decode("utf-8")
                return json.loads(raw) if raw.strip() else {"success": True}
        except Exception as e:
            print(f"[BlueskyClient XRPC POST] {endpoint} error: {e}")
            return {}

    # --- Direct Messages (Chat) Helpers ---
    def chat_xrpc(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        payload: Optional[Dict[str, Any]] = None,
        method: str = "GET",
    ) -> Dict[str, Any]:
        """Routes chat.bsky.convo.* requests with the required atproto-proxy header."""
        from .runtime import may_publish
        if method == "POST" and (self.dry_run or not may_publish()):
            return {"simulated": True}
        if not self.dm_available:
            return {}
        if not self.ensure_session():
            return {}

        headers = {
            "Authorization": f"Bearer {self.jwt}",
            "atproto-proxy": "did:web:api.bsky.chat#bsky_chat",
        }
        url = f"{config.bsky_chat_base}/{endpoint}"
        if params:
            url = f"{url}?{urllib.parse.urlencode(params)}"

        data = None
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"

        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code in (400, 401, 403):
                # Check for token scope error (app password created without DM permissions)
                try:
                    err_body = e.read().decode("utf-8")
                    if "Token is not authorized" in err_body or "scope" in err_body.lower():
                        print("[BlueskyClient] DM scope not enabled on this app password. Skipping DMs.")
                        self.dm_available = False
                        return {}
                except Exception:
                    pass
            print(f"[BlueskyClient Chat] {endpoint} HTTPError {e.code}: {e.reason}")
            return {}
        except Exception as e:
            print(f"[BlueskyClient Chat] {endpoint} error: {type(e).__name__}")
            return {}

    # --- Feed & Content Reading ---
    def get_timeline(self, limit: int = 25) -> List[Dict[str, Any]]:
        """Retrieves user's home timeline."""
        res = self.xrpc_get("app.bsky.feed.getTimeline", {"limit": limit})
        return res.get("feed", [])

    def search_posts(self, query: str, limit: int = 15) -> List[Dict[str, Any]]:
        """Searches posts across Bluesky."""
        from .recency import MAX_POST_AGE
        since = (dt.datetime.now(dt.timezone.utc) - MAX_POST_AGE).isoformat().replace("+00:00", "Z")
        res = self.xrpc_get("app.bsky.feed.searchPosts", {"q": query, "limit": limit, "sort":"latest", "since":since})
        return res.get("posts", [])

    def get_saved_feed_uris(self) -> List[str]:
        """Retrieves pinned/saved Bluesky custom feed URIs from actor preferences (cached per session)."""
        from .runtime import MODE
        if MODE.get() == "offline":
            return []
        if self._saved_feed_uris is not None:
            return list(self._saved_feed_uris)
        res = self.xrpc_get("app.bsky.actor.getPreferences")
        prefs = res.get("preferences", []) if isinstance(res, dict) else []
        pinned: List[str] = []
        saved: List[str] = []
        for pref in prefs:
            if not isinstance(pref, dict):
                continue
            ptype = pref.get("$type", "")
            if ptype == "app.bsky.actor.defs#savedFeedsPrefV2":
                for item in pref.get("items", []):
                    if not isinstance(item, dict) or item.get("type") != "feed":
                        continue
                    val = item.get("value", "")
                    if isinstance(val, str) and val.startswith("at://"):
                        if item.get("pinned"):
                            pinned.append(val)
                        else:
                            saved.append(val)
            elif ptype == "app.bsky.actor.defs#savedFeedsPref":
                for val in pref.get("pinned", []):
                    if isinstance(val, str) and val.startswith("at://"):
                        pinned.append(val)
                for val in pref.get("saved", []):
                    if isinstance(val, str) and val.startswith("at://"):
                        saved.append(val)
        uris = list(dict.fromkeys(pinned + saved))
        self._saved_feed_uris = uris
        return list(uris)

    def get_custom_feed(self, feed_uri: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Retrieves posts from a Bluesky custom feed generator."""
        if not feed_uri:
            return []
        res = self.xrpc_get("app.bsky.feed.getFeed", {"feed": feed_uri, "limit": limit})
        return res.get("feed", []) if isinstance(res, dict) else []

    def discover_popular_feeds(self, query: str, limit: int = 3) -> List[Dict[str, Any]]:
        """Finds popular, safe Bluesky custom feed generators matching a topic query."""
        if not query:
            return []
        res = self.xrpc_get("app.bsky.unspecced.getPopularFeedGenerators", {"query": query, "limit": limit})
        feeds = res.get("feeds", []) if isinstance(res, dict) else []
        unsafe_terms = ("18+", "nsfw", "🔞", "porn", "xxx", "erotic", "onlyfans", "fetish", "hentai", "야동", "성인")
        adult_labels = {"porn", "sexual", "nudity", "graphic-media"}
        safe_feeds: List[Dict[str, Any]] = []
        for fg in feeds:
            if not isinstance(fg, dict):
                continue
            text = f"{fg.get('displayName') or ''}\n{fg.get('description') or ''}".lower()
            if any(term in text for term in unsafe_terms):
                continue
            raw_labels = fg.get("labels") or []
            label_vals = {
                str(lb.get("val", "") if isinstance(lb, dict) else lb).lower()
                for lb in raw_labels
            }
            if label_vals & adult_labels:
                continue
            safe_feeds.append(fg)
        return safe_feeds

    def get_author_feed(self, actor: str, limit: int = 4) -> List[Dict[str, Any]]:
        """Retrieves recent original posts for an author (posts_no_replies)."""
        if not actor:
            return []
        res = self.xrpc_get("app.bsky.feed.getAuthorFeed", {"actor": actor, "limit": limit, "filter": "posts_no_replies"})
        return res.get("feed", []) if isinstance(res, dict) else []

    def get_discovery_feed(
        self,
        limit: int = 25,
        topics: Optional[List[str]] = None,
        follower_dids: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Retrieves discovery feed posts:
        Combines timeline posts from followed accounts with custom feeds, new-follower posts,
        and dynamic topic searches.
        Returns normalized list of candidate items [{'post': post_dict, 'source': ...}, ...].
        """
        items: List[Dict[str, Any]] = []
        seen_uris: Set[str] = set()
        from .recency import post_recency
        from .runtime import MODE

        # 1. Timeline posts from followed accounts
        timeline = self.get_timeline(limit=15)
        for t in timeline:
            p = t.get("post", t) if isinstance(t, dict) else {}
            u = p.get("uri")
            if u and u not in seen_uris and post_recency(p) == "recent":
                seen_uris.add(u)
                items.append({"post": p, "source": "timeline"})

        # Optional curiosity derived only from public continuity, never a random topic rotation.
        from .discussion import discovery_queries
        chosen_topics = topics[:2] if topics is not None else discovery_queries()

        # 2. Custom feeds (configured or saved; fallback to popular feed discovery if none configured)
        if topics is None and MODE.get() != "offline":
            feed_entries: List[Tuple[str, str]] = []
            seen_feed_uris: Set[str] = set()
            for uri in list(config.custom_feed_uris) + self.get_saved_feed_uris():
                if isinstance(uri, str) and uri.startswith("at://") and uri not in seen_feed_uris:
                    seen_feed_uris.add(uri)
                    label = uri.rstrip("/").split("/")[-1][:24] or "custom"
                    feed_entries.append((uri, label))

            selected_feeds: List[Tuple[str, str]] = []
            if feed_entries:
                if len(feed_entries) <= 2:
                    selected_feeds = feed_entries
                else:
                    slot = int(dt.datetime.now(dt.timezone.utc).timestamp() // 3600) % len(feed_entries)
                    selected_feeds = [feed_entries[slot], feed_entries[(slot + 1) % len(feed_entries)]]
            elif config.enable_custom_feed_discovery and chosen_topics:
                for fg in self.discover_popular_feeds(chosen_topics[0], limit=2):
                    uri = fg.get("uri", "") if isinstance(fg, dict) else ""
                    if isinstance(uri, str) and uri.startswith("at://"):
                        label = str(fg.get("displayName") or uri.rstrip("/").split("/")[-1])[:24]
                        selected_feeds.append((uri, label))
                        break

            for feed_uri, label in selected_feeds:
                for fp in self.get_custom_feed(feed_uri, limit=8):
                    p = fp.get("post", fp) if isinstance(fp, dict) else {}
                    u = p.get("uri") if isinstance(p, dict) else None
                    if u and u not in seen_uris and post_recency(p) == "recent":
                        seen_uris.add(u)
                        items.append({"post": p, "source": f"feed:{label}"})

        # 3. Topic search posts
        for topic in chosen_topics:
            search_res = self.search_posts(topic, limit=8)
            for p in search_res:
                u = p.get("uri")
                if u and u not in seen_uris and post_recency(p) == "recent":
                    seen_uris.add(u)
                    items.append({"post": p, "source": f"search:{topic}"})

        # 4. Recent posts from newly arrived followers
        if follower_dids and MODE.get() != "offline":
            for did in list(dict.fromkeys(follower_dids))[:2]:
                if not did:
                    continue
                for ap in self.get_author_feed(did, limit=2):
                    p = ap.get("post", ap) if isinstance(ap, dict) else {}
                    u = p.get("uri") if isinstance(p, dict) else None
                    if u and u not in seen_uris and post_recency(p) == "recent":
                        seen_uris.add(u)
                        items.append({"post": p, "source": "new_follower"})
                        break

        # Interleave observation sources so a full timeline cannot hide all discovery results.
        from itertools import zip_longest
        groups = {}
        for item in items:
            groups.setdefault(item["source"], []).append(item)
        return [item for row in zip_longest(*groups.values()) for item in row if item is not None][:limit]

    @staticmethod
    def _is_safe_bsky_image_url(url: str) -> bool:
        """Allows only HTTPS image URLs served from official Bluesky CDN hosts."""
        if not isinstance(url, str) or not url.strip():
            return False
        try:
            p = urllib.parse.urlsplit(url.strip())
            return (
                p.scheme == "https"
                and p.hostname in {"cdn.bsky.app", "av-cdn.bsky.app"}
                and not p.username
                and not p.password
                and p.port in (None, 443)
            )
        except (ValueError, TypeError):
            return False

    @classmethod
    def extract_image_urls(cls, post_dict: Dict[str, Any]) -> List[str]:
        """
        Safely extracts hydrated Bluesky CDN image URLs (preferring thumb over fullsize)
        from a post view or quoted embed view.
        """
        if not isinstance(post_dict, dict):
            return []
        embed = post_dict.get("embed") or {}
        if not isinstance(embed, dict):
            return []

        image_lists: List[Any] = []
        if isinstance(embed.get("images"), list):
            image_lists.append(embed["images"])
        if isinstance(embed.get("media", {}).get("images"), list):
            image_lists.append(embed["media"]["images"])

        rec_view = embed.get("record", {})
        if isinstance(rec_view, dict):
            nested_rec = rec_view.get("record") if isinstance(rec_view.get("record"), dict) else rec_view
            for sub_embed in (nested_rec.get("embeds") or []) if isinstance(nested_rec, dict) else []:
                if isinstance(sub_embed, dict):
                    if isinstance(sub_embed.get("images"), list):
                        image_lists.append(sub_embed["images"])
                    if isinstance(sub_embed.get("media", {}).get("images"), list):
                        image_lists.append(sub_embed["media"]["images"])

        urls: List[str] = []
        for images in image_lists:
            for img in images:
                if not isinstance(img, dict):
                    continue
                candidate = str(img.get("thumb") or img.get("fullsize") or "").strip()
                if cls._is_safe_bsky_image_url(candidate) and candidate not in urls:
                    urls.append(candidate)
                    if len(urls) >= 4:
                        return urls
        return urls

    @classmethod
    def has_attached_images(cls, post_dict: Dict[str, Any]) -> bool:
        """Returns True if a post view or raw notification record contains image embeds."""
        if not isinstance(post_dict, dict):
            return False
        if cls.extract_image_urls(post_dict):
            return True
        record_embed = post_dict.get("record", {}).get("embed") or {}
        if isinstance(record_embed, dict):
            imgs = record_embed.get("images") or record_embed.get("media", {}).get("images") or []
            if isinstance(imgs, list) and imgs:
                return True
        return False

    def fetch_post_images(self, urls: List[str], max_images: int = 2) -> List[str]:
        """
        Downloads up to max_images safe Bluesky CDN images and converts them into
        compact data:image/jpeg;base64 URLs for multimodal vision inspection.
        Never fetches in offline mode.
        """
        from .runtime import MODE
        if MODE.get() == "offline" or not urls or max_images <= 0:
            return []
        from .generator import _encode_review_image_data_url
        import requests

        data_urls: List[str] = []
        for url in dict.fromkeys(urls):
            if len(data_urls) >= max_images:
                break
            if not self._is_safe_bsky_image_url(url):
                continue
            try:
                with requests.get(
                    url,
                    timeout=(4, 8),
                    stream=True,
                    allow_redirects=False,
                    headers={"User-Agent": "SeoyeonVision/1.0"},
                ) as resp:
                    if resp.status_code != 200:
                        continue
                    ctype = resp.headers.get("Content-Type", "").lower()
                    if not ctype.startswith("image/"):
                        continue
                    body = bytearray()
                    too_large = False
                    for chunk in resp.iter_content(8192):
                        body.extend(chunk)
                        if len(body) > 5_000_000:
                            too_large = True
                            break
                    if too_large or not body:
                        continue
                    data_urls.append(_encode_review_image_data_url(bytes(body)))
            except Exception:
                continue
        return data_urls

    @staticmethod
    def extract_image_alt_texts(post_dict: Dict[str, Any]) -> List[str]:
        """
        Safely extracts user-provided accessibility alt text from image embeds.
        Returns a list of sanitized alt text strings.
        """
        if not isinstance(post_dict, dict):
            return []
        embed = post_dict.get("embed") or {}
        record_embed = post_dict.get("record", {}).get("embed") or {}
        images = []
        if isinstance(embed, dict):
            images = embed.get("images") or embed.get("media", {}).get("images") or []
        if not images and isinstance(record_embed, dict):
            images = record_embed.get("images") or record_embed.get("media", {}).get("images") or []

        alt_texts = []
        if isinstance(images, list):
            for img in images:
                if isinstance(img, dict) and img.get("alt"):
                    alt = str(img["alt"]).strip()
                    if alt:
                        from .validator import ContentValidator
                        alt_texts.append(ContentValidator.sanitize_untrusted_input(alt))
        return alt_texts

    @classmethod
    def extract_embed_summary(cls, post_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Safely extracts readable quoted-post text and external link-card metadata from a post embed."""
        if not isinstance(post_dict, dict):
            return {}
        embed = post_dict.get("embed") or {}
        if not isinstance(embed, dict):
            return {}

        from .validator import ContentValidator
        summary: Dict[str, Any] = {}

        rec_container = embed.get("record")
        if isinstance(rec_container, dict):
            view_rec = rec_container.get("record") if isinstance(rec_container.get("record"), dict) else rec_container
            if isinstance(view_rec, dict):
                val = view_rec.get("value") if isinstance(view_rec.get("value"), dict) else view_rec.get("record")
                q_text = val.get("text", "") if isinstance(val, dict) else ""
                if isinstance(q_text, str) and q_text.strip():
                    q_author = (view_rec.get("author") or {}).get("handle", "")
                    summary["quoted_post"] = {
                        "author": str(q_author),
                        "text": ContentValidator.sanitize_untrusted_input(q_text)[:350],
                        "uri": str(view_rec.get("uri") or ""),
                    }

        ext = embed.get("external")
        if not isinstance(ext, dict) and isinstance(embed.get("media"), dict):
            ext = embed["media"].get("external")
        if isinstance(ext, dict):
            title = str(ext.get("title") or "").strip()
            desc = str(ext.get("description") or "").strip()
            uri = str(ext.get("uri") or "").strip()
            if title or desc or uri:
                summary["external_card"] = {
                    "title": ContentValidator.sanitize_untrusted_input(title)[:140],
                    "description": ContentValidator.sanitize_untrusted_input(desc)[:220],
                    "uri": uri,
                }

        return summary

    def get_thread_context(self, uri: str, depth: int = 4) -> Dict[str, Any]:
        """
        Retrieves thread details to obtain complete conversation context
        including root post, intermediate parents, sibling replies, and embed summaries.
        """
        encoded_uri = urllib.parse.quote(uri)
        res = self.xrpc_get("app.bsky.feed.getPostThread", {"uri": uri, "depth": depth})
        thread = res.get("thread", {})

        posts_chain: List[Dict[str, Any]] = []
        curr = thread
        while curr and curr.get("$type") == "app.bsky.feed.defs#threadViewPost":
            p = curr.get("post", {})
            if p:
                posts_chain.append({
                    "uri": p.get("uri"),
                    "cid": p.get("cid"),
                    "author": p.get("author", {}).get("handle", ""),
                    "author_did": p.get("author", {}).get("did", ""),
                    "text": p.get("record", {}).get("text", ""),
                    "links": [f.get("uri") for facet in p.get("record", {}).get("facets", [])
                              for f in facet.get("features", []) if f.get("$type") == "app.bsky.richtext.facet#link"],
                    "media_present_not_inspected": bool(p.get("embed")),
                    "media_alt_texts": self.extract_image_alt_texts(p),
                    "media_urls": self.extract_image_urls(p),
                    "embed_summary": self.extract_embed_summary(p),
                })
            parent_node = curr.get("parent")
            if parent_node and parent_node.get("$type") == "app.bsky.feed.defs#threadViewPost":
                curr = parent_node
            else:
                break

        # Reverse chain so it goes Root -> Parent -> Current
        posts_chain.reverse()

        sibling_replies: List[Dict[str, str]] = []
        raw_replies = thread.get("replies") if isinstance(thread, dict) else None
        if isinstance(raw_replies, list):
            from .validator import ContentValidator
            ranked_siblings = []
            for rep in raw_replies:
                if not isinstance(rep, dict) or rep.get("$type") != "app.bsky.feed.defs#threadViewPost":
                    continue
                rp = rep.get("post", {})
                r_text = (rp.get("record") or {}).get("text", "") if isinstance(rp, dict) else ""
                if not isinstance(r_text, str) or not r_text.strip():
                    continue
                likes = rp.get("likeCount", 0) or 0
                ranked_siblings.append((
                    likes,
                    {
                        "author": str((rp.get("author") or {}).get("handle", "")),
                        "text": ContentValidator.sanitize_untrusted_input(r_text)[:240],
                    },
                ))
            ranked_siblings.sort(key=lambda item: item[0], reverse=True)
            sibling_replies = [item[1] for item in ranked_siblings[:3]]

        return {
            "thread": thread,
            "chain": posts_chain,
            "root": posts_chain[0] if posts_chain else None,
            "current": posts_chain[-1] if posts_chain else None,
            "sibling_replies": sibling_replies,
        }

    def can_reply_to_thread(
        self,
        target_uri: str,
        thread_ctx: Optional[Dict[str, Any]] = None,
    ) -> Tuple[bool, str]:
        """
        In-situ verification against the live AT Protocol post thread:
        Enforces the invariant:
        'Never comment on the same post twice without another comment in between by another user.'

        Returns (True, "OK") if safe, or (False, reason) if replying would violate the invariant.
        """
        if not target_uri:
            return False, "Empty target URI"

        if not thread_ctx:
            thread_ctx = self.get_thread_context(target_uri)

        thread = thread_ctx.get("thread", {}) if isinstance(thread_ctx, dict) else {}
        if not thread or thread.get("$type") != "app.bsky.feed.defs#threadViewPost":
            # If thread structure is not accessible (e.g. simulated dry-run or deleted post),
            # allow default progression (memory layer acts as defense).
            return True, "Thread unverified or unavailable"

        target_post = thread.get("post", {})
        target_author = target_post.get("author", {})
        target_handle = (target_author.get("handle") or "").lower()
        target_did = target_author.get("did") or ""

        my_handle = (self.handle or config.bsky_handle or "").lower()
        my_did = self.did or ""

        # 1. Target post authored by self -> cannot reply to self
        if (my_handle and target_handle == my_handle) or (my_did and target_did == my_did):
            return False, "Target post was authored by Seo-yeon herself"

        # 2. Check direct replies under target_post
        replies = thread.get("replies", [])
        if isinstance(replies, list):
            for rep in replies:
                if not isinstance(rep, dict) or rep.get("$type") != "app.bsky.feed.defs#threadViewPost":
                    continue
                rep_post = rep.get("post", {})
                rep_author = rep_post.get("author", {})
                rep_handle = (rep_author.get("handle") or "").lower()
                rep_did = rep_author.get("did") or ""

                if (my_handle and rep_handle == my_handle) or (my_did and rep_did == my_did):
                    # Seo-yeon has already posted a reply to this target_post!
                    # Check if another user has replied to Seo-yeon's reply:
                    child_replies = rep.get("replies", [])
                    has_subsequent_user_reply = False
                    if isinstance(child_replies, list):
                        for cr in child_replies:
                            if isinstance(cr, dict) and cr.get("$type") == "app.bsky.feed.defs#threadViewPost":
                                cr_author = cr.get("post", {}).get("author", {})
                                cr_handle = (cr_author.get("handle") or "").lower()
                                cr_did = cr_author.get("did") or ""
                                if (my_handle and cr_handle != my_handle) and (not my_did or cr_did != my_did):
                                    has_subsequent_user_reply = True
                                    break

                    if not has_subsequent_user_reply:
                        return False, "Seo-yeon already commented on this post without another comment in between by another user"
                    else:
                        return False, "Seo-yeon already commented directly on this post; any reply must target the subsequent comment"

        return True, "Safe to reply"

    # --- Notifications ---
    def list_notifications(self, limit: int = 30) -> List[Dict[str, Any]]:
        res = self.xrpc_get("app.bsky.notification.listNotifications", {"limit": limit})
        return res.get("notifications", [])

    def update_seen(self) -> None:
        if self.dry_run:
            return
        now_iso = dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")
        self.xrpc_post("app.bsky.notification.updateSeen", {"seenAt": now_iso})

    # --- Direct Messages ---
    def list_convos(self, limit: int = 15) -> List[Dict[str, Any]]:
        res = self.chat_xrpc("chat.bsky.convo.listConvos", params={"limit": limit})
        return res.get("convos", [])

    def get_convo_messages(self, convo_id: str, limit: int = 15) -> List[Dict[str, Any]]:
        res = self.chat_xrpc("chat.bsky.convo.getMessages", params={"convoId": convo_id, "limit": limit})
        return sorted(res.get("messages", []), key=lambda m: (m.get("sentAt", ""), m.get("id", "")))

    def send_dm(self, convo_id: str, text: str) -> Dict[str, Any]:
        from .runtime import may_publish
        if self.dry_run or not may_publish():
            print("[PREVIEW] Private reply prepared; not sent.")
            return {"simulated": True, "convoId": convo_id}
        from .delivery import Outbox, action_key
        endpoint = "chat.bsky.convo.sendMessage"
        key = action_key(endpoint, convo_id + ":" + (getattr(self, "action_identity", "") or text))
        def lookup(saved):
            for msg in self.get_convo_messages(convo_id, limit=50):
                if (msg.get("sender", {}).get("did") == self.did and msg.get("text") == saved["message"]["text"]
                    and msg.get("sentAt", "") >= saved.get("_prepared_at", "")):
                    return {"id": msg["id"]}
            return None
        payload = {"convoId": convo_id, "message": {"text": text}, "_prepared_at": dt.datetime.now(dt.timezone.utc).isoformat()}
        def transport(ep, body):
            return self.chat_xrpc(ep, payload={k:v for k,v in body.items() if not k.startswith("_")}, method="POST")
        identity = getattr(self, "action_identity", "")
        payload["_incoming_id"] = identity.split(":", 1)[1] if identity.startswith("ANSWER_DM:") else ""
        receipt = Outbox().send(key, endpoint, payload, transport, lookup)
        if receipt.get("id"):
            from .memory_store import memory_store
            memory_store.record_recent_dm(receipt["id"])
            memory_store.mark_dm_handled(payload["_incoming_id"])
        return receipt

    def mark_convo_read(self, convo_id: str, message_id: str) -> None:
        if self.dry_run:
            return
        self.chat_xrpc(
            "chat.bsky.convo.updateRead",
            payload={"convoId": convo_id, "messageId": message_id},
            method="POST",
        )

    # --- Publishing & Likes ---
    @staticmethod
    def detect_langs(text: str) -> List[str]:
        """Infers Bluesky language tags from outgoing text without mislabeling single-language posts."""
        if not isinstance(text, str) or not text.strip():
            return ["ko", "en"]
        stripped = re.sub(r"https?://[^\s]+", " ", text)
        stripped = re.sub(r"@[a-zA-Z0-9._-]+", " ", stripped)
        hangul = len(re.findall(r"[\uac00-\ud7a3]", stripped))
        latin = len(re.findall(r"[A-Za-z]", stripped))
        if hangul > 0 and latin == 0:
            return ["ko"]
        if latin > 0 and hangul == 0:
            return ["en"]
        if hangul > 0 and latin > 0:
            if hangul >= 3 and latin >= 15:
                return ["ko", "en"]
            return ["ko"] if hangul >= 3 else ["en"]
        return ["ko", "en"]

    @staticmethod
    def parse_facets(text: str) -> List[Dict[str, Any]]:
        """Parses hashtags and URLs, formatting them as AT Protocol facets with UTF-8 byte offsets."""
        facets = []
        # 1. Hashtags
        tag_pattern = re.compile(r'(?:^|\s)(#([^\s#.,!?:;()\[\]{}"\'<>]+))')
        for match in tag_pattern.finditer(text):
            tag_val = match.group(2)
            start_char = match.start(1)
            end_char = match.end(1)
            start_byte = len(text[:start_char].encode("utf-8"))
            end_byte = len(text[:end_char].encode("utf-8"))
            facets.append({
                "index": {"byteStart": start_byte, "byteEnd": end_byte},
                "features": [{"$type": "app.bsky.richtext.facet#tag", "tag": tag_val}],
            })

        # 2. URLs / links
        url_pattern = re.compile(r'https?://[^\s]+')
        for match in url_pattern.finditer(text):
            url_val = match.group(0).rstrip(".,!?:;)]}")
            start_char = match.start(0)
            end_char = start_char + len(url_val)
            start_byte = len(text[:start_char].encode("utf-8"))
            end_byte = len(text[:end_char].encode("utf-8"))
            facets.append({
                "index": {"byteStart": start_byte, "byteEnd": end_byte},
                "features": [{"$type": "app.bsky.richtext.facet#link", "uri": url_val}],
            })

        facets.sort(key=lambda f: f["index"]["byteStart"])
        return facets

    def build_facets(self, text: str) -> List[Dict[str, Any]]:
        """Builds hashtag, link, and @mention facets (DID resolution skipped when offline or dry-run)."""
        facets = self.parse_facets(text)
        from .runtime import MODE
        mention_pattern = re.compile(
            r'(?:^|(?<=[\s(]))(@([a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)+))'
        )
        for match in mention_pattern.finditer(text):
            handle = match.group(2).lower()
            start_char = match.start(1)
            end_char = match.end(1)
            start_byte = len(text[:start_char].encode("utf-8"))
            end_byte = len(text[:end_char].encode("utf-8"))
            if any(f["index"]["byteStart"] <= start_byte < f["index"]["byteEnd"] for f in facets):
                continue
            if handle in self._did_cache:
                did = self._did_cache[handle]
            elif MODE.get() != "offline" and not self.dry_run:
                did = self.resolve_handle(handle)
                self._did_cache[handle] = did
            else:
                did = None
            if did:
                facets.append({
                    "index": {"byteStart": start_byte, "byteEnd": end_byte},
                    "features": [{"$type": "app.bsky.richtext.facet#mention", "did": did}],
                })
        facets.sort(key=lambda f: f["index"]["byteStart"])
        return facets

    def upload_image_blob(self, image_bytes: bytes) -> Optional[Dict[str, Any]]:
        """Compresses image to <950KB JPEG and uploads blob via com.atproto.repo.uploadBlob."""
        if not self.ensure_session():
            return None

        # Recompress via Pillow if needed
        try:
            im = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            buf = io.BytesIO()
            quality = 90
            im.save(buf, format="JPEG", quality=quality, optimize=True)
            while buf.tell() > 950_000 and quality > 50:
                buf.seek(0)
                buf.truncate(0)
                quality -= 5
                im.save(buf, format="JPEG", quality=quality, optimize=True)
            compressed_bytes = buf.getvalue()
        except Exception:
            compressed_bytes = image_bytes

        if self.dry_run:
            print(f"[DRY-RUN] Would upload image blob ({len(compressed_bytes)} bytes)")
            return {
                "$type": "blob",
                "ref": {"$link": "simulated-blob-cid"},
                "mimeType": "image/jpeg",
                "size": len(compressed_bytes),
            }

        url = f"{config.bsky_xrpc_base}/com.atproto.repo.uploadBlob"
        req = urllib.request.Request(
            url,
            data=compressed_bytes,
            headers={"Content-Type": "image/jpeg", "Authorization": f"Bearer {self.jwt}"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                res = json.loads(resp.read().decode("utf-8"))
                return res.get("blob")
        except Exception as e:
            print(f"[BlueskyClient] Failed to upload image blob: {e}")
            return None

    def publish_text_post(self, text: str, langs: Optional[List[str]] = None) -> Dict[str, Any]:
        """Publishes an original text post."""
        if not self.ensure_session():
            return {}

        now_iso = dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")
        record: Dict[str, Any] = {
            "$type": "app.bsky.feed.post",
            "text": text,
            "createdAt": now_iso,
            "langs": langs or self.detect_langs(text),
        }
        facets = self.build_facets(text)
        if facets:
            record["facets"] = facets

        if self.dry_run:
            print(f"[DRY-RUN] Would publish text post: \"{text}\"")
            return {"uri": "at://did:plc:simulated/app.bsky.feed.post/simulated", "cid": "sim-cid"}

        return self.xrpc_post(
            "com.atproto.repo.createRecord",
            {"repo": self.did, "collection": "app.bsky.feed.post", "record": record},
        )

    def publish_image_post(
        self,
        text: str,
        image_bytes,
        alt_text="Seo-yeon candid snapshot",
        langs: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Publishes an image post with text. Accepts one image (bytes) or a list of up to 4 with matching alt texts."""
        images_in = [image_bytes] if isinstance(image_bytes, (bytes, bytearray)) else list(image_bytes or [])
        images_in = images_in[:4]
        if not images_in:
            return {}
        if isinstance(alt_text, str):
            alts = [alt_text] if len(images_in) == 1 else [alt_text] + [""] * (len(images_in) - 1)
        else:
            alts = [str(a) for a in (alt_text or [])]
            alts = (alts + [""] * len(images_in))[:len(images_in)]

        embeds = []
        for data, alt in zip(images_in, alts):
            blob = self.upload_image_blob(bytes(data))
            if not blob:
                print("[BlueskyClient] Blob upload failed; aborting image post without text fallback.")
                return {}
            embeds.append({"alt": alt, "image": blob})

        if not self.ensure_session():
            return {}

        now_iso = dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")
        record: Dict[str, Any] = {
            "$type": "app.bsky.feed.post",
            "text": text,
            "createdAt": now_iso,
            "langs": langs or self.detect_langs(text),
            "embed": {
                "$type": "app.bsky.embed.images",
                "images": embeds,
            },
        }
        facets = self.build_facets(text)
        if facets:
            record["facets"] = facets

        if self.dry_run:
            print(f"[DRY-RUN] Would publish image post ({len(embeds)} image(s)): \"{text}\"")
            self.last_dry_run_record = record
            return {"uri": "at://did:plc:simulated/app.bsky.feed.post/simulated", "cid": "sim-cid"}

        return self.xrpc_post(
            "com.atproto.repo.createRecord",
            {"repo": self.did, "collection": "app.bsky.feed.post", "record": record},
        )

    def delete_post(self, post_uri_or_rkey: str) -> bool:
        """Deletes a post from Bluesky repository via com.atproto.repo.deleteRecord."""
        if self.dry_run:
            print(f"[DRY-RUN] Would delete post: {post_uri_or_rkey}")
            return True
        if not self.ensure_session():
            return False
        rkey = post_uri_or_rkey.rstrip("/").split("/")[-1]
        res = self.xrpc_post(
            "com.atproto.repo.deleteRecord",
            {
                "repo": self.did,
                "collection": "app.bsky.feed.post",
                "rkey": rkey,
            },
        )
        return res is not None

    def publish_reply(
        self,
        reply_text: str,
        parent_uri: str,
        parent_cid: str,
        root_uri: str,
        root_cid: str,
        langs: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Publishes a reply in a thread."""
        if not self.ensure_session():
            return {}

        now_iso = dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")
        record: Dict[str, Any] = {
            "$type": "app.bsky.feed.post",
            "text": reply_text,
            "createdAt": now_iso,
            "langs": langs or self.detect_langs(reply_text),
            "reply": {
                "root": {"uri": root_uri, "cid": root_cid},
                "parent": {"uri": parent_uri, "cid": parent_cid},
            },
        }
        facets = self.build_facets(reply_text)
        if facets:
            record["facets"] = facets

        if self.dry_run:
            print(f"[DRY-RUN] Would publish reply: \"{reply_text}\" to {parent_uri}")
            return {"uri": "at://did:plc:simulated/app.bsky.feed.post/simulated", "cid": "sim-cid"}

        return self.xrpc_post(
            "com.atproto.repo.createRecord",
            {"repo": self.did, "collection": "app.bsky.feed.post", "record": record},
        )

    def like_post(self, uri: str, cid: str) -> Dict[str, Any]:
        """Likes a post."""
        if not self.ensure_session():
            return {}

        now_iso = dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")
        record = {
            "$type": "app.bsky.feed.like",
            "subject": {"uri": uri, "cid": cid},
            "createdAt": now_iso,
        }

        if self.dry_run:
            print(f"[DRY-RUN] Would like post: {uri}")
            return {"uri": "at://did:plc:simulated/app.bsky.feed.like/simulated"}

        return self.xrpc_post(
            "com.atproto.repo.createRecord",
            {"repo": self.did, "collection": "app.bsky.feed.like", "record": record},
        )

    def resolve_handle(self, handle: str) -> Optional[str]:
        """Resolves a handle to its DID."""
        clean_handle = handle.lstrip("@").strip()
        res = self.xrpc_get("com.atproto.identity.resolveHandle", {"handle": clean_handle})
        return res.get("did")

    def repost(self, uri: str, cid: str) -> Dict[str, Any]:
        """Reposts a post on Bluesky."""
        if not self.ensure_session():
            return {}
        now_iso = dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")
        record = {
            "$type": "app.bsky.feed.repost",
            "subject": {"uri": uri, "cid": cid},
            "createdAt": now_iso,
        }
        if self.dry_run:
            print(f"[DRY-RUN] Would repost: {uri}")
            return {"uri": f"at://{self.did}/app.bsky.feed.repost/simulated"}

        return self.xrpc_post(
            "com.atproto.repo.createRecord",
            {"repo": self.did, "collection": "app.bsky.feed.repost", "record": record},
        )

    def quote_post(self, text: str, target_uri: str, target_cid: str, langs: Optional[List[str]] = None) -> Dict[str, Any]:
        """Quote-posts an existing post with commentary."""
        if not self.ensure_session():
            return {}
        now_iso = dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")
        record: Dict[str, Any] = {
            "$type": "app.bsky.feed.post",
            "text": text,
            "createdAt": now_iso,
            "langs": langs or self.detect_langs(text),
            "embed": {
                "$type": "app.bsky.embed.record",
                "record": {"uri": target_uri, "cid": target_cid},
            },
        }
        facets = self.build_facets(text)
        if facets:
            record["facets"] = facets

        if self.dry_run:
            print(f"[DRY-RUN] Would quote post {target_uri}: \"{text}\"")
            return {"uri": f"at://{self.did}/app.bsky.feed.post/simulated", "cid": "sim-cid"}

        return self.xrpc_post(
            "com.atproto.repo.createRecord",
            {"repo": self.did, "collection": "app.bsky.feed.post", "record": record},
        )

    def follow(self, subject_did: str) -> Dict[str, Any]:
        """Follows an account on Bluesky."""
        if not self.ensure_session():
            return {}
        now_iso = dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")
        record = {
            "$type": "app.bsky.graph.follow",
            "subject": subject_did,
            "createdAt": now_iso,
        }
        if self.dry_run:
            print(f"[DRY-RUN] Would follow: {subject_did}")
            return {"uri": f"at://{self.did}/app.bsky.graph.follow/simulated"}

        return self.xrpc_post(
            "com.atproto.repo.createRecord",
            {"repo": self.did, "collection": "app.bsky.graph.follow", "record": record},
        )

    def update_profile(
        self,
        display_name: Optional[str] = None,
        description: Optional[str] = None,
        avatar_bytes: Optional[bytes] = None,
        banner_bytes: Optional[bytes] = None,
    ) -> Dict[str, Any]:
        """Updates the actor's profile record (displayName, description, avatar, banner)."""
        if not self.ensure_session():
            return {}

        existing = self.xrpc_get("com.atproto.repo.getRecord", {
            "repo": self.did,
            "collection": "app.bsky.actor.profile",
            "rkey": "self",
        })
        val = existing.get("value", {}) if isinstance(existing, dict) else {}

        # Start from the full existing record so fields this method does not manage (links, labels,
        # pinned post, ...) are preserved rather than silently dropped.
        record: Dict[str, Any] = dict(val)
        record["$type"] = "app.bsky.actor.profile"
        record["displayName"] = display_name if display_name is not None else val.get("displayName", "")
        record["description"] = description if description is not None else val.get("description", "")
        if "createdAt" in val:
            record["createdAt"] = val["createdAt"]
        else:
            record["createdAt"] = dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")

        if avatar_bytes:
            blob = self.upload_image_blob(avatar_bytes)
            if blob:
                record["avatar"] = blob
        elif "avatar" in val:
            record["avatar"] = val["avatar"]

        if banner_bytes:
            blob = self.upload_image_blob(banner_bytes)
            if blob:
                record["banner"] = blob
        elif "banner" in val:
            record["banner"] = val["banner"]

        if self.dry_run:
            print(f"[DRY-RUN] Would update profile: {record.get('displayName')} | {record.get('description')}")
            return {"uri": f"at://{self.did}/app.bsky.actor.profile/self"}

        return self.xrpc_post(
            "com.atproto.repo.putRecord",
            {
                "repo": self.did,
                "collection": "app.bsky.actor.profile",
                "rkey": "self",
                "record": record,
            },
        )


bsky_client = BlueskyClient()
