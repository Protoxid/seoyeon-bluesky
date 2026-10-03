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
from typing import Any, Dict, List, Optional, Tuple

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
                return json.loads(resp.read().decode("utf-8"))
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
            print(f"[BlueskyClient Chat] {endpoint} error: {e}")
            return {}

    # --- Feed & Content Reading ---
    def get_timeline(self, limit: int = 25) -> List[Dict[str, Any]]:
        """Retrieves user's home timeline."""
        res = self.xrpc_get("app.bsky.feed.getTimeline", {"limit": limit})
        return res.get("feed", [])

    def search_posts(self, query: str, limit: int = 15) -> List[Dict[str, Any]]:
        """Searches posts across Bluesky."""
        res = self.xrpc_get("app.bsky.feed.searchPosts", {"q": query, "limit": limit})
        return res.get("posts", [])

    def get_thread_context(self, uri: str, depth: int = 4) -> Dict[str, Any]:
        """
        Retrieves thread details to obtain complete conversation context
        including root post, intermediate parents, and author details.
        """
        encoded_uri = urllib.parse.quote(uri)
        res = self.xrpc_get(f"app.bsky.feed.getPostThread?uri={encoded_uri}&depth={depth}")
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
                    "text": p.get("record", {}).get("text", ""),
                })
            parent_node = curr.get("parent")
            if parent_node and parent_node.get("$type") == "app.bsky.feed.defs#threadViewPost":
                curr = parent_node
            else:
                break

        # Reverse chain so it goes Root -> Parent -> Current
        posts_chain.reverse()
        return {
            "thread": thread,
            "chain": posts_chain,
            "root": posts_chain[0] if posts_chain else None,
            "current": posts_chain[-1] if posts_chain else None,
        }

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
        return res.get("messages", [])

    def send_dm(self, convo_id: str, text: str) -> Dict[str, Any]:
        if self.dry_run:
            print(f"[DRY-RUN] Would send DM to {convo_id}: \"{text}\"")
            return {"simulated": True, "convoId": convo_id, "text": text}
        return self.chat_xrpc(
            "chat.bsky.convo.sendMessage",
            payload={"convoId": convo_id, "message": {"text": text}},
            method="POST",
        )

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
    def parse_facets(text: str) -> List[Dict[str, Any]]:
        """Parses hashtags and formats them as AT Protocol facets."""
        facets = []
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
            "langs": langs or ["ko", "en"],
        }
        facets = self.parse_facets(text)
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
        image_bytes: bytes,
        alt_text: str = "Seo-yeon candid snapshot",
        langs: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Publishes an image post with text."""
        blob = self.upload_image_blob(image_bytes)
        if not blob:
            # Fall back to text post if blob upload failed
            print("[BlueskyClient] Blob upload failed, falling back to text post.")
            return self.publish_text_post(text, langs=langs)

        if not self.ensure_session():
            return {}

        now_iso = dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")
        record: Dict[str, Any] = {
            "$type": "app.bsky.feed.post",
            "text": text,
            "createdAt": now_iso,
            "langs": langs or ["ko", "en"],
            "embed": {
                "$type": "app.bsky.embed.images",
                "images": [{"alt": alt_text, "image": blob}],
            },
        }
        facets = self.parse_facets(text)
        if facets:
            record["facets"] = facets

        if self.dry_run:
            print(f"[DRY-RUN] Would publish image post: \"{text}\"")
            return {"uri": "at://did:plc:simulated/app.bsky.feed.post/simulated", "cid": "sim-cid"}

        return self.xrpc_post(
            "com.atproto.repo.createRecord",
            {"repo": self.did, "collection": "app.bsky.feed.post", "record": record},
        )

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
            "langs": langs or ["ko", "en"],
            "reply": {
                "root": {"uri": root_uri, "cid": root_cid},
                "parent": {"uri": parent_uri, "cid": parent_cid},
            },
        }

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


bsky_client = BlueskyClient()
