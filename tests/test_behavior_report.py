import contextlib
import datetime as dt
import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path

SPEC = importlib.util.spec_from_file_location("behavior_report", Path(__file__).resolve().parents[1] / "scripts" / "behavior_report.py")
behavior_report = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(behavior_report)


class TestBehaviorReport(unittest.TestCase):
    def test_counts_topics_and_flags_fixation_without_other_peoples_text(self):
        now = dt.datetime.now(dt.timezone.utc)
        with tempfile.TemporaryDirectory() as tmp:
            data = Path(tmp)
            (data / "logs").mkdir()
            (data / "memory").mkdir()
            rows = [{"ts": now.isoformat(), "action": "PUBLISH_TEXT_POST", "executed": True, "dry_run": False,
                     "details": {"selection": "original_pass"}},
                    {"ts": now.isoformat(), "action": "BROWSE_AND_REPLY", "executed": True, "dry_run": False,
                     "details": {"reply_text": "a reply that must not be printed"}}]
            (data / "logs" / "tick_history.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
            posts = [{"text": f"허리가 뻣뻣하다 {i}", "created_at": now.isoformat(), "has_image": i == 0} for i in range(6)]
            (data / "memory" / "recent_context.json").write_text(json.dumps({"posts": posts}), encoding="utf-8")
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                behavior_report.report(data, 7)
        text = out.getvalue()
        self.assertIn("PUBLISH_TEXT_POST=1", text)
        self.assertIn("original_pass=1", text)
        self.assertIn("photos: 1", text)
        self.assertIn("possible fixation: 'pilates/body'", text)
        self.assertNotIn("must not be printed", text)


if __name__ == "__main__":
    unittest.main()
