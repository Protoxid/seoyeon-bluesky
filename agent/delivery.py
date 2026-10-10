"""Durable action outbox. Ambiguous DM delivery is held for reconciliation."""
from __future__ import annotations
import hashlib
import json
import os
import subprocess
from .storage import read_json, write_json, file_lock


def checkpoint():
    from .vault import vault
    vault.save_vault()
    if os.environ.get("SEOYEON_GIT_CHECKPOINT") != "1":
        return
    from .config import PROJECT_ROOT
    def git(*args):
        result = subprocess.run(["git", *args], cwd=PROJECT_ROOT, capture_output=True)
        if result.returncode:
            raise RuntimeError("Durable state checkpoint failed; outbound work stopped")
        return result.stdout
    for relative in ("data/vault.enc", "data/budget_ledger.json", "data/memory", "data/logs/tick_history.jsonl"):
        if (PROJECT_ROOT / relative).exists():
            git("add", "--", relative)
    if git("diff", "--cached", "--name-only"):
        git("commit", "-m", "chore(agent): checkpoint delivery state [skip ci]")
    # Never send if the durable checkpoint cannot reach the remote repository.
    git("push", "origin", "HEAD:main")


class Outbox:
    def __init__(self, path=None, persist=None):
        from .vault import vault
        self.path = path or vault.vault_dir / "outbox.json"
        self.persist = persist or checkpoint

    def prepare(self, key, endpoint, payload):
        with file_lock(self.path):
            data = read_json(self.path, {})
            if key not in data:
                # Freeze the payload before sending; retries cannot change its text/time.
                data[key] = {"endpoint": endpoint, "payload": payload,
                             "status": "prepared", "receipt": None, "accounted": False}
                write_json(self.path, data)
                self.persist()
            return data[key]

    def update(self, key, **changes):
        with file_lock(self.path):
            data = read_json(self.path, {})
            data[key].update(changes)
            write_json(self.path, data)
            self.persist()

    def send(self, key, endpoint, payload, transport, lookup=None, *, idempotent=False):
        item = self.prepare(key, endpoint, payload)
        if item["status"] == "abandoned":
            return {}
        if item["status"] == "delivered":
            return item["receipt"]
        if item["status"] == "uncertain":
            receipt = lookup(item["payload"]) if lookup else None
            if receipt:
                self.update(key, status="delivered", receipt=receipt)
                return receipt
            if not idempotent:
                return {}  # A timed-out DM is not automatically sent twice.
        self.update(key, status="uncertain")
        result = transport(endpoint, item["payload"])
        if result and (result.get("uri") or result.get("id")):
            self.update(key, status="delivered", receipt=result)
            return result
        receipt = lookup(item["payload"]) if lookup else None
        if receipt:
            self.update(key, status="delivered", receipt=receipt)
            return receipt
        return {}

    def pending(self):
        return {k:v for k,v in read_json(self.path, {}).items() if v["status"] not in {"delivered", "abandoned"}}


def action_key(endpoint, identity):
    return hashlib.sha256((endpoint + ":" + identity).encode()).hexdigest()[:32]


def recover_delivery():
    """Reconcile interrupted records; ambiguous non-idempotent sends remain held."""
    from .bsky_client import bsky_client as client
    from .memory_store import memory_store as memory
    outbox = Outbox()
    clear = True
    for key, item in read_json(outbox.path, {}).items():
        if item["status"] == "abandoned":
            continue
        endpoint, payload = item["endpoint"], item["payload"]
        receipt = item.get("receipt") or {}
        if endpoint == "com.atproto.repo.createRecord":
            def lookup(saved):
                result = client.xrpc_get("com.atproto.repo.getRecord", {k:saved[k] for k in ("repo", "collection", "rkey")})
                return result if result.get("uri") else None
            if item["status"] != "delivered":
                receipt = outbox.send(key, endpoint, payload, client._xrpc_post_raw, lookup, idempotent=True)
            if receipt.get("uri") and not item.get("accounted"):
                record = payload["record"]
                if payload["collection"] == "app.bsky.feed.post":
                    parent = record.get("reply", {}).get("parent", {}).get("uri", "")
                    if parent:
                        memory.record_recent_reply("", "", record.get("text", ""), uri=receipt["uri"], target_uri=parent)
                    else:
                        memory.record_recent_post(record.get("text", ""), "recovered", receipt["uri"], bool(record.get("embed", {}).get("images")))
                elif payload["collection"] == "app.bsky.feed.like":
                    memory.record_recent_like(record["subject"]["uri"])
                outbox.update(key, accounted=True)
        elif endpoint == "chat.bsky.convo.sendMessage" and item["status"] != "delivered":
            for message in client.get_convo_messages(payload["convoId"], limit=50):
                if (message.get("sender", {}).get("did") == client.did
                    and message.get("text") == payload["message"]["text"]
                    and message.get("sentAt", "") >= payload.get("_prepared_at", "")):
                    receipt = {"id": message["id"]}
                    outbox.update(key, status="delivered", receipt=receipt)
                    break
        if endpoint == "chat.bsky.convo.sendMessage" and receipt.get("id") and not item.get("accounted"):
            memory.mark_dm_handled(payload.get("_incoming_id", ""))
            memory.record_recent_dm(receipt["id"], payload.get("_prepared_at"))
            if not item.get("accounted"):
                outbox.update(key, accounted=True)
        if not receipt:
            clear = False
    return clear
