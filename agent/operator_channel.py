"""Encrypted operator conversation and restart-safe command stages."""
import json
from pathlib import Path
from .storage import read_json, write_json, file_lock

# Runtime capabilities, not fictional possessions or evidence of completion.
CAPABILITIES = {
    "PUBLISH_IMAGE_POST": "Generate and publish a fictional selfie using two canonical face references, or a POV image. No physical phone, camera, saved photo or real-world photoshoot is required. Subject to budget, provider availability and image review.",
    "PUBLISH_TEXT_POST": "Draft, review and publish a Bluesky post.",
    "BROWSE_AND_REPLY": "Browse notifications and feed, choose a suitable conversation and reply.",
    "BROWSE_AND_LIKE": "Browse and like an eligible post.",
    "ANSWER_DM": "Process eligible Bluesky direct messages.",
    "CONSOLIDATE": "Consolidate stored memories.",
}

class OperatorChannel:
    def __init__(self, path=None, persist=None):
        if path is None:
            from .vault import vault
            path=vault.vault_dir / "operator_channel.json"
        from .delivery import checkpoint
        self.path=Path(path); self.persist=persist or checkpoint
    def load(self):
        return read_json(self.path,{"turns":{},"checkins":"meaningful","notes":{},"alerts":{}})
    def update(self, key, **changes):
        with file_lock(self.path):
            data=self.load(); row=data["turns"].setdefault(str(key),{})
            row.update(changes); write_json(self.path,data); self.persist()
            return row
    def history(self):
        rows=[v for v in self.load()["turns"].values() if v.get("ack_sent")]
        return [{"inbound":r.get("inbound", "")[:1200], "reply":r.get("reply", "")[:1200],
                 "result":r.get("result", {}), "partial":len(r.get("inbound", ""))>1200 or len(r.get("reply", ""))>1200}
                for r in rows[-8:]]
    def pending_request(self):
        """Only the latest delivered clarification may be continued, for 24 hours."""
        from datetime import datetime, timezone
        rows=list(self.load()["turns"].items())
        if not rows: return None
        key,row=rows[-1]
        directive=row.get("directive",{})
        if row.get("stage")!="done" or not row.get("ack_sent") or not directive.get("pending_action"):
            return None
        try:
            age=(datetime.now(timezone.utc)-datetime.fromisoformat(row["created_at"])).total_seconds()
            if not 0 <= age <= 86400: return None
        except (KeyError, ValueError, TypeError): return None
        return {"id":key,"action_type":directive["pending_action"],
                "image_kind":directive.get("image_kind","unspecified"),
                "request":row.get("inbound", ""),"clarification":row.get("reply", "")}

    def setting(self, mode):
        if mode not in {"meaningful","daily","off"}: raise ValueError("Invalid check-in preference")
        with file_lock(self.path):
            data=self.load(); data["checkins"]=mode; write_json(self.path,data); self.persist()
    def record(self, collection, key, value):
        with file_lock(self.path):
            data=self.load(); data.setdefault(collection,{})[key]=value
            write_json(self.path,data); self.persist()

    def resolve(self, key, evidence):
        if not evidence.strip(): raise ValueError("Review evidence required")
        with file_lock(self.path):
            data=self.load(); row=data["turns"].get(str(key))
            if not row or row.get("stage")!="running": raise ValueError("Unknown interrupted command")
            row.update(stage="done",result={"status":"operator_reviewed_no_retry","evidence":evidence})
            write_json(self.path,data); self.persist()
