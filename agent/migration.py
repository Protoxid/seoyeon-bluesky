"""Quarantine legacy unscoped memories before using the new continuity store."""
import json
from .storage import read_json, write_json


def migrate_legacy_state(memory_dir, vault):
    archive_file = vault.vault_dir / "legacy_unscoped.json"
    archive = read_json(archive_file, {})
    changed = []
    episodic = memory_dir / "episodic_memory.jsonl"
    if episodic.exists():
        rows = [json.loads(line) for line in episodic.read_text(encoding="utf-8").splitlines() if line.strip()]
        def clean(value):
            if isinstance(value, dict):
                return {k:clean(v) for k,v in value.items() if k not in {"journal_excerpt", "journal_text"}}
            if isinstance(value, list):
                return [clean(v) for v in value]
            return value
        private = [row for row in rows if clean(row) != row]
        if private:
            archive.setdefault("journal_metadata", []).extend(private)
            sanitized = [clean(row) for row in rows]
            changed.append((episodic, sanitized, True))
    narrative = memory_dir / "narrative_state.json"
    data = read_json(narrative, {})
    if data.get("open_loops"):
        archive.setdefault("open_loops", []).extend(data["open_loops"])
        data["open_loops"] = []
        changed.append((narrative, data, False))
    if not changed:
        return
    write_json(archive_file, archive)
    if not vault.save_vault():
        raise RuntimeError("Legacy archive was not encrypted; migration stopped")
    for path, content, jsonl in changed:
        if jsonl:
            import os
            temporary = path.with_suffix(".migration.tmp")
            temporary.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in content), encoding="utf-8")
            os.replace(temporary, path)
        else:
            write_json(path, content)
