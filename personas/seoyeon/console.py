#!/usr/bin/env python3
"""
console.py — the local control panel for the Seo-yeon project.

    python console.py            then open http://127.0.0.1:8765

TWO SCREENS, and deliberately only two:
    GENERATE   pick shots, see what a run will cost, cap it, run it, watch it,
               and keep an honest running total of what has been spent.
    PUBLISH    the caption desk: caption, tags, location, alt text, export to
               1080x1440, mark posted.

THE ONE ARCHITECTURAL RULE: this file NEVER reimplements generation or export.
It shells out to `outside.py` and `publish_prep.py`. Every rule in CLAUDE.md —
the assembled prompt blocks, the no-face routing, the tier map, the crop anchor
— lives in those scripts and must keep living in exactly one place. A console
that built its own prompts would drift from the CLI within a week and then the
playbook would be true of only one of them.

Consequences of that rule, on purpose:
  * The prompt a shot will send is obtained by running `outside.py --dry-run`
    and reading what it prints. Not by importing a builder. Not by guessing.
  * The cost of a run is the number `outside.py` itself prints, divided by the
    images it was going to make. We do not keep a second price table.
  * The export is `publish_prep.py`, so the 3:4 rule and the 0.70 crop anchor
    are the ones already reasoned about.

STDLIB ONLY. No Flask, no pip install. This has to start on a machine I cannot
inspect, so it may not depend on anything that might not be there. Pillow is
imported lazily and only for thumbnails; without it the console still runs and
shows full-size images instead.

api.kie.ai is blocked from the cloud container and from device_bash. Every
generation runs here, on this machine, through this file's subprocess. That is
the whole reason this is a local server and not a hosted page.
"""
from __future__ import annotations

import json
import mimetypes
import os
import pathlib
import re
import subprocess
import sys
import threading
import time
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROOT = pathlib.Path(__file__).resolve().parent
PORT = int(os.environ.get("CONSOLE_PORT", "8765"))
POSTS = ROOT / "posts.json"
SPEND = ROOT / "spend.jsonl"
THUMBS = ROOT / "_thumbs"

# pool -> (shots module, attribute, CLI flags, output folder)
# The CLI flags are the authority. If outside.py grows a pool, add it here and
# nowhere else.
POOLS = {
    "grid":        ("grid_shots",   "SHOTS", ["--grid"],                 "content/grid"),
    "grid_reel":   ("grid_shots",   "REEL",  ["--grid", "--reel"],       "content/grid_reel"),
    "week":        ("week_shots",   "SHOTS", ["--week"],                 "content/week"),
    "week2":       ("week2_shots",  "SHOTS", ["--week2"],                "content/week2"),
    "plates":      ("pov",          "PLATES", ["--plates"],              "content/plates"),
    "week2_reel":  ("week2_shots",  "REEL",  ["--week2", "--w2reel"],    "content/week2_reel"),
    "reel_frames": ("reel_frames",  "SHOTS", ["--reel-frames"],          "content/reel_frames"),
    "fanvue":      ("fanvue_shots", "SHOTS", ["--fanvue"],               "content/fanvue"),
    "outside":     ("outside_shots", "SHOTS", [],                        "content/outside"),
    "lora":        ("lora_shots",   "SHOTS", ["--lora"],                 "content/lora"),
    "w37":         ("w37_shots",    "SHOTS", ["--week3"],                "content/w37_2026-09-07"),
}

# ---------------------------------------------------------------- run state --

class Run:
    """One generation subprocess. There is at most one at a time, on purpose:
    two concurrent runs would race on the budget and neither total would be
    true."""

    def __init__(self):
        self.lock = threading.Lock()
        self.proc: subprocess.Popen | None = None
        self.lines: list[str] = []
        self.started = 0.0
        self.finished = 0.0
        self.cmd: list[str] = []
        self.meta: dict = {}

    @property
    def running(self) -> bool:
        return self.proc is not None and self.proc.poll() is None

    def start(self, cmd: list[str], meta: dict) -> tuple[bool, str]:
        with self.lock:
            if self.running:
                return False, "a run is already going"
            self.lines = []
            self.cmd = cmd
            self.meta = meta
            self.started = time.time()
            self.finished = 0.0
            # -u so the child's prints arrive line by line instead of in one
            # lump at the end. Without it the progress view is a blank box
            # followed by everything at once, which is not progress.
            env = {**os.environ, "PYTHONUTF8": "1"}
            self.proc = subprocess.Popen(
                cmd, cwd=str(ROOT), stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT, text=True, bufsize=1,
                encoding="utf-8", errors="replace", env=env)
            threading.Thread(target=self._pump, daemon=True).start()
            return True, "started"

    def _pump(self):
        assert self.proc and self.proc.stdout
        for line in self.proc.stdout:
            self.lines.append(line.rstrip("\n"))
        self.proc.wait()
        self.finished = time.time()
        self._record()

    def _record(self):
        """Append what actually happened to spend.jsonl.

        The cost written down is the one outside.py PRINTS, not the one the
        console estimated, because the script refunds a failed image and the
        estimate does not know that."""
        text = "\n".join(self.lines)
        m = re.search(r"~\$([0-9.]+)\s*->", text)
        reported = float(m.group(1)) if m else None
        ok = len(re.findall(r"\]\s+ok\s", text))
        fail = len(re.findall(r"\]\s+FAIL\s", text))
        row = dict(ts=time.time(), cmd=self.cmd[1:], ok=ok, fail=fail,
                   estimated=self.meta.get("estimated"), reported=reported,
                   pool=self.meta.get("pool"), model=self.meta.get("model"),
                   ids=self.meta.get("ids", []))
        try:
            with open(SPEND, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(row) + "\n")
        except OSError:
            pass

    def snapshot(self, since: int) -> dict:
        return dict(running=self.running, lines=self.lines[since:],
                    total=len(self.lines),
                    seconds=round((self.finished or time.time()) - self.started, 1)
                    if self.started else 0)


RUN = Run()

# -------------------------------------------------------------- pool facts --

_pool_cache: dict[str, tuple[float, dict]] = {}


def _shots_file(pool: str) -> pathlib.Path:
    return ROOT / (POOLS[pool][0] + ".py")


def pool_facts(pool: str) -> dict:
    """Shots, their assembled-prompt hashes, and what is on disk.

    Cached against the mtime of the shots file AND of outside.py, so editing a
    prompt OR a shared block invalidates it and nothing has to be restarted.
    outside.py matters because SKIN, ARMS, ROLES and SAFE live there: change
    one of those and every assembled prompt in every pool changes with it. A
    cache keyed only on the shots file would have gone on showing yesterday's
    hashes and quietly reporting stale renders as current."""
    stamp = 0.0
    for src in (_shots_file(pool), ROOT / "outside.py"):
        if src.exists():
            stamp += src.stat().st_mtime
    hit = _pool_cache.get(pool)
    if hit and hit[0] == stamp:
        return hit[1]
    facts = _build_pool_facts(pool)
    _pool_cache[pool] = (stamp, facts)
    return facts


def _dry_run(pool: str, model: str) -> tuple[dict[str, str], float]:
    """Ask outside.py what it would send, and what it would cost.

    Returns {shot id: assembled prompt} and the per-image price. Parsing the
    CLI's own output is the point: it cannot disagree with itself."""
    flags, _ = POOLS[pool][2], POOLS[pool][3]
    cmd = [sys.executable, "-Xutf8", "-u", "outside.py", *flags, "--all",
           "--model", model, "--dry-run"]
    try:
        out = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True,
                             timeout=120, encoding="utf-8", errors="replace").stdout
    except (OSError, subprocess.SubprocessError):
        return {}, 0.0

    unit = 0.0
    m = re.search(r"\s(\d+)\s+image\(s\)\s+~\$([0-9.]+)", out)
    if m and int(m.group(1)):
        unit = float(m.group(2)) / int(m.group(1))

    prompts: dict[str, str] = {}
    for block in out.split("=" * 66)[1:]:
        lines = block.split("\n")
        idx = next((i for i, l in enumerate(lines)
                    if re.match(r"\[\S+\s+\S+\]", l.strip())), None)
        if idx is None:
            continue
        sid = re.match(r"\[(\S+)", lines[idx].strip()).group(1)
        prompts[sid] = "\n".join(lines[idx + 1:]).rstrip("\n")
    return prompts, unit


def _build_pool_facts(pool: str) -> dict:
    mod, attr, _flags, outdir = POOLS[pool]
    shots = []
    try:
        sys.path.insert(0, str(ROOT))
        m = __import__(mod)
        shots = list(getattr(m, attr, []) or [])
    except Exception as e:                                  # noqa: BLE001
        return dict(pool=pool, error=f"{mod}.py: {e}", shots=[], unit=0.0,
                    outdir=outdir)

    out = {}
    for model in ("gpt",):        # the renderer. others resolved on demand.
        out[model] = _dry_run(pool, model)
    prompts, unit = out["gpt"]

    import hashlib
    folder = ROOT / outdir
    rows = []
    for d in shots:
        sid = d["id"]
        prompt = prompts.get(sid, "")
        h = hashlib.sha256(prompt.encode()).hexdigest()[:6] if prompt else ""
        renders = sorted(folder.glob(f"{sid}_*_*.png")) if folder.exists() else []
        current = [p for p in renders if h and f"_{h}_" in p.name]
        newest = max(renders, key=lambda p: p.stat().st_mtime) if renders else None
        rows.append(dict(
            id=sid, day=d.get("day", ""), tier=d.get("tier", ""),
            aspect=d.get("aspect", "3:4"),
            flags=[k for k in ("noface", "selfie", "limb", "body", "safe")
                   if d.get(k)],
            story=(d.get("story") or "")[:180],
            text=d.get("text", ""),
            prompt=prompt, hash=h,
            renders=len(renders),
            current=[rel(p) for p in current],
            newest=rel(newest) if newest else "",
            # A locked shot is one whose PUBLISHED version passed QC.
            # Its prompt may have been rewritten since for future use, and
            # that hash difference is not a defect. Locked beats stale so
            # "select stale" can never sweep an accepted frame into a
            # regeneration batch.
            locked=bool(d.get("locked")),
            stale=bool(renders) and not current and not d.get("locked"),
            missing=not renders and not d.get("locked"),
        ))
    return dict(pool=pool, shots=rows, unit=round(unit, 4), outdir=outdir,
                error="")


def rel(p: pathlib.Path) -> str:
    try:
        return p.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return ""


# ------------------------------------------------------------------ posts --

def load_posts() -> list[dict]:
    if not POSTS.exists():
        return []
    try:
        return json.loads(POSTS.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []


def save_posts(rows: list[dict]) -> None:
    tmp = POSTS.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(rows, indent=1, ensure_ascii=False),
                   encoding="utf-8")
    tmp.replace(POSTS)


def spend_summary() -> dict:
    total = 0.0
    today = 0.0
    n = 0
    day0 = time.time() - (time.time() % 86400)
    if SPEND.exists():
        for line in SPEND.read_text(encoding="utf-8").splitlines():
            try:
                r = json.loads(line)
            except ValueError:
                continue
            c = r.get("reported")
            if c is None:
                continue
            total += c
            n += r.get("ok", 0)
            if r.get("ts", 0) >= day0:
                today += c
    return dict(total=round(total, 2), today=round(today, 2), images=n)


# ------------------------------------------------------------------- HTTP --

def thumb(relpath: str, width: int = 420) -> tuple[bytes, str] | None:
    src = (ROOT / relpath).resolve()
    if not str(src).startswith(str(ROOT)) or not src.is_file():
        return None
    try:
        from PIL import Image                                # noqa: PLC0415
    except ImportError:
        return src.read_bytes(), mimetypes.guess_type(src.name)[0] or "image/png"
    THUMBS.mkdir(exist_ok=True)
    key = relpath.replace("/", "__") + f".{width}.jpg"
    dest = THUMBS / key
    if not dest.exists() or dest.stat().st_mtime < src.stat().st_mtime:
        im = Image.open(src).convert("RGB")
        im.thumbnail((width, width * 4), Image.LANCZOS)
        im.save(dest, quality=85)
    return dest.read_bytes(), "image/jpeg"


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *a):                                # quiet
        pass

    # -- plumbing --
    def _send(self, code: int, body: bytes, ctype: str):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def _json(self, obj, code=200):
        self._send(code, json.dumps(obj, ensure_ascii=False).encode("utf-8"),
                   "application/json; charset=utf-8")

    def _body(self) -> dict:
        n = int(self.headers.get("Content-Length") or 0)
        if not n:
            return {}
        try:
            return json.loads(self.rfile.read(n).decode("utf-8"))
        except ValueError:
            return {}

    # -- routes --
    def do_GET(self):
        u = urllib.parse.urlparse(self.path)
        q = urllib.parse.parse_qs(u.query)
        p = u.path

        if p in ("/", "/index.html"):
            return self._send(200, PAGE.encode("utf-8"), "text/html; charset=utf-8")

        if p == "/api/pool":
            name = (q.get("name") or ["grid"])[0]
            if name not in POOLS:
                return self._json({"error": "unknown pool"}, 404)
            return self._json(pool_facts(name))

        if p == "/api/pools":
            return self._json({"pools": list(POOLS), "spend": spend_summary()})

        if p == "/api/run":
            since = int((q.get("since") or ["0"])[0])
            return self._json(RUN.snapshot(since))

        if p == "/api/posts":
            return self._json({"posts": load_posts()})

        if p == "/img":
            rp = (q.get("p") or [""])[0]
            src = (ROOT / rp).resolve()
            if not str(src).startswith(str(ROOT)) or not src.is_file():
                return self._send(404, b"no", "text/plain")
            return self._send(200, src.read_bytes(),
                              mimetypes.guess_type(src.name)[0] or "image/png")

        if p == "/thumb":
            rp = (q.get("p") or [""])[0]
            w = int((q.get("w") or ["420"])[0])
            got = thumb(rp, w)
            if not got:
                return self._send(404, b"no", "text/plain")
            return self._send(200, got[0], got[1])

        return self._send(404, b"no", "text/plain")

    def do_POST(self):
        p = urllib.parse.urlparse(self.path).path
        b = self._body()

        if p == "/api/run":
            pool = b.get("pool", "grid")
            ids = [i for i in b.get("ids", []) if i]
            model = b.get("model", "gpt")
            budget = float(b.get("budget", 0) or 0)
            n = int(b.get("n", 1) or 1)
            if pool not in POOLS:
                return self._json({"ok": False, "error": "unknown pool"}, 400)
            if not ids:
                return self._json({"ok": False, "error": "nothing selected"}, 400)
            unit = pool_facts(pool).get("unit", 0.0)
            est = round(unit * len(ids) * n, 2)
            # The cap is the safety rail, so it is never inferred. If the
            # caller did not set one, the estimate itself becomes the cap.
            cap = budget if budget > 0 else max(est, 0.01)
            if est > cap + 1e-9:
                return self._json({"ok": False,
                                   "error": f"estimate ${est:.2f} exceeds cap "
                                            f"${cap:.2f}"}, 400)
            cmd = [sys.executable, "-u", "outside.py", *POOLS[pool][2],
                   "--only", ",".join(ids), "--model", model,
                   "--n", str(n), "--budget", f"{cap:.2f}"]
            ok, msg = RUN.start(cmd, dict(pool=pool, model=model, ids=ids,
                                          estimated=est))
            return self._json({"ok": ok, "error": "" if ok else msg,
                               "cmd": " ".join(cmd[1:]), "estimated": est})

        if p == "/api/run/dryrun":
            pool = b.get("pool", "grid")
            ids = [i for i in b.get("ids", []) if i]
            model = b.get("model", "gpt")
            if pool not in POOLS or not ids:
                return self._json({"ok": False, "error": "nothing selected"}, 400)
            cmd = [sys.executable, "-u", "outside.py", *POOLS[pool][2],
                   "--only", ",".join(ids), "--model", model, "--dry-run"]
            ok, msg = RUN.start(cmd, dict(pool=pool, model=model, ids=ids,
                                          estimated=0.0))
            return self._json({"ok": ok, "error": "" if ok else msg})

        if p == "/api/posts":
            rows = b.get("posts")
            if not isinstance(rows, list):
                return self._json({"ok": False, "error": "bad payload"}, 400)
            save_posts(rows)
            return self._json({"ok": True, "n": len(rows)})

        if p == "/api/export":
            src = b.get("image", "")
            anchor = float(b.get("anchor", 0.70))
            kind = b.get("kind", "feed")
            f = (ROOT / src).resolve()
            if not str(f).startswith(str(ROOT)) or not f.is_file():
                return self._json({"ok": False, "error": "no such image"}, 400)
            cmd = [sys.executable, "-u", "publish_prep.py", rel(f),
                   "--kind", kind, "--anchor", str(anchor)]
            try:
                r = subprocess.run(cmd, cwd=str(ROOT), capture_output=True,
                                   text=True, timeout=180, encoding="utf-8",
                                   errors="replace")
            except (OSError, subprocess.SubprocessError) as e:
                return self._json({"ok": False, "error": str(e)}, 500)
            tag = f.parent.name if f.parent.name not in ("content", "heroes") else ""
            stem = f"{tag}__{f.stem}" if tag else f.stem
            dest = f"publish/{kind}/{stem}.jpg"
            exists = (ROOT / dest).is_file()
            return self._json({"ok": exists, "out": r.stdout.strip(),
                               "path": dest if exists else "",
                               "error": "" if exists else "publish_prep wrote nothing"})

        return self._json({"error": "no route"}, 404)


# ------------------------------------------------------------------- page --

PAGE = r"""<!doctype html><html><head><meta charset="utf-8">
<title>Seo-yeon console</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
:root{--bg:#101113;--card:#17181b;--line:#2a2c31;--ink:#e8e6e3;--dim:#9a9691;
      --acc:#c9a227;--bad:#c9564a;--ok:#5c9e6b}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
     font:14px/1.5 ui-sans-serif,-apple-system,Segoe UI,Roboto,sans-serif}
header{display:flex;gap:18px;align-items:center;padding:12px 18px;
       border-bottom:1px solid var(--line);position:sticky;top:0;
       background:var(--bg);z-index:9}
h1{font-size:15px;margin:0;font-weight:600;letter-spacing:.02em}
nav button{background:none;border:0;color:var(--dim);font:inherit;
           padding:6px 10px;cursor:pointer;border-radius:6px}
nav button.on{color:var(--ink);background:var(--card)}
.spend{margin-left:auto;color:var(--dim);font-variant-numeric:tabular-nums}
.spend b{color:var(--ink)}
main{padding:18px;max-width:1500px;margin:0 auto}
.bar{display:flex;gap:12px;align-items:center;flex-wrap:wrap;margin-bottom:14px}
select,input,textarea{background:var(--card);color:var(--ink);
  border:1px solid var(--line);border-radius:6px;padding:6px 8px;font:inherit}
textarea{width:100%;resize:vertical;line-height:1.55}
button.go{background:var(--acc);color:#1a1408;border:0;border-radius:6px;
  padding:8px 16px;font:inherit;font-weight:600;cursor:pointer}
button.go[disabled]{opacity:.4;cursor:not-allowed}
button.ghost{background:var(--card);color:var(--ink);border:1px solid var(--line);
  border-radius:6px;padding:7px 12px;font:inherit;cursor:pointer}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:14px}
.card{background:var(--card);border:1px solid var(--line);border-radius:9px;
      overflow:hidden;cursor:pointer;position:relative}
.card.sel{outline:2px solid var(--acc);outline-offset:-2px}
.card img{width:100%;display:block;aspect-ratio:3/4;object-fit:cover;
          background:#000}
.card .none{aspect-ratio:3/4;display:grid;place-items:center;color:var(--dim);
            font-size:12px;background:#0b0c0d}
.meta{padding:8px 10px}
.meta .id{font-weight:600;font-size:13px}
.meta .sub{color:var(--dim);font-size:11.5px;margin-top:2px}
.pill{display:inline-block;font-size:10.5px;padding:1px 6px;border-radius:99px;
      border:1px solid var(--line);color:var(--dim);margin:3px 3px 0 0}
.pill.stale{border-color:var(--bad);color:var(--bad)}
.pill.missing{border-color:var(--acc);color:var(--acc)}
pre.log{background:#0b0c0d;border:1px solid var(--line);border-radius:8px;
  padding:12px;max-height:340px;overflow:auto;white-space:pre-wrap;
  font:12px/1.55 ui-monospace,Menlo,Consolas,monospace;margin:0}
.post{background:var(--card);border:1px solid var(--line);border-radius:9px;
  padding:14px;display:grid;grid-template-columns:200px 1fr;gap:16px;
  margin-bottom:14px}
.post img{width:100%;border-radius:6px;display:block}
.row{display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin-top:8px}
label.lab{color:var(--dim);font-size:11.5px;display:block;margin-bottom:3px;
  text-transform:uppercase;letter-spacing:.06em}
.warn{color:var(--bad);font-size:12px}
.good{color:var(--ok);font-size:12px}
.hint{color:var(--dim);font-size:12px;margin:6px 0 0}
dialog{background:var(--card);color:var(--ink);border:1px solid var(--line);
  border-radius:10px;max-width:min(1100px,94vw);padding:0}
dialog::backdrop{background:#000c}
.dlg{display:grid;grid-template-columns:1fr 1fr;gap:0}
.dlg img{width:100%;display:block;border-radius:10px 0 0 10px}
.dlg .side{padding:16px;max-height:80vh;overflow:auto}
.dlg pre{white-space:pre-wrap;font:12px/1.6 ui-monospace,Menlo,Consolas,monospace;
  background:#0b0c0d;border:1px solid var(--line);border-radius:6px;padding:10px}
</style></head><body>
<header>
  <h1>seo-yeon console</h1>
  <nav>
    <button id="tGen" class="on" onclick="tab('gen')">generate</button>
    <button id="tPub" onclick="tab('pub')">publish</button>
  </nav>
  <div class="spend" id="spend"></div>
</header>
<main>
  <section id="gen">
    <div class="bar">
      <select id="pool" onchange="loadPool()"></select>
      <select id="model">
        <option value="gpt">gpt-image-2 (the renderer)</option>
        <option value="qwen">qwen3</option>
        <option value="seedream">seedream</option>
      </select>
      <button class="ghost" onclick="pick('stale')">select stale</button>
      <button class="ghost" onclick="pick('missing')">select missing</button>
      <button class="ghost" onclick="pick('none')">clear</button>
      <span style="margin-left:auto"></span>
      <label class="lab" style="margin:0">cap&nbsp;$</label>
      <input id="budget" size="5" value="0.50">
      <button class="ghost" onclick="run(true)">dry run</button>
      <button class="go" id="goBtn" onclick="run(false)">generate</button>
    </div>
    <p class="hint" id="est"></p>
    <pre class="log" id="log" style="display:none"></pre>
    <div class="grid" id="cards"></div>
  </section>

  <section id="pub" style="display:none">
    <div class="bar">
      <button class="ghost" onclick="addPost()">+ add post</button>
      <button class="go" onclick="savePosts()">save</button>
      <span class="hint" id="psave"></span>
    </div>
    <div id="posts"></div>
  </section>
</main>

<dialog id="dlg"><div class="dlg">
  <img id="dimg" alt="">
  <div class="side">
    <div class="lab">shot</div><div id="did" style="font-weight:600"></div>
    <div class="lab" style="margin-top:12px">story</div>
    <div id="dstory" style="color:var(--dim)"></div>
    <div class="lab" style="margin-top:12px">prompt as sent</div>
    <pre id="dprompt"></pre>
    <button class="ghost" onclick="dlg.close()">close</button>
  </div>
</div></dialog>

<script>
let POOL = null, SEL = new Set(), POSTS = [], SINCE = 0, TIMER = null;

const $ = s => document.querySelector(s);
const esc = s => (s||"").replace(/[&<>"]/g, c =>
  ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));

function tab(w){
  $("#gen").style.display = w==="gen" ? "" : "none";
  $("#pub").style.display = w==="pub" ? "" : "none";
  $("#tGen").className = w==="gen" ? "on" : "";
  $("#tPub").className = w==="pub" ? "on" : "";
  if(w==="pub") loadPosts();
}

async function boot(){
  const r = await (await fetch("/api/pools")).json();
  $("#pool").innerHTML = r.pools.map(p=>`<option>${p}</option>`).join("");
  showSpend(r.spend);
  loadPool();
}
function showSpend(s){
  $("#spend").innerHTML =
    `today <b>$${s.today.toFixed(2)}</b> &nbsp; all time <b>$${s.total.toFixed(2)}</b>`
    + ` &nbsp; <span style="opacity:.6">${s.images} images</span>`;
}

async function loadPool(){
  const name = $("#pool").value;
  $("#cards").innerHTML = `<p class="hint">reading ${name}… (this runs a dry
    run of outside.py, which takes a moment)</p>`;
  POOL = await (await fetch("/api/pool?name="+encodeURIComponent(name))).json();
  SEL.clear(); draw();
}

function draw(){
  if(POOL.error){ $("#cards").innerHTML = `<p class="warn">${esc(POOL.error)}</p>`; return; }
  $("#cards").innerHTML = POOL.shots.map(s=>{
    const img = s.newest
      ? `<img loading="lazy" src="/thumb?w=440&p=${encodeURIComponent(s.newest)}">`
      : `<div class="none">never rendered</div>`;
    const pills = [
      s.missing ? `<span class="pill missing">no render</span>` : "",
      s.locked  ? `<span class="pill">locked \u00b7 QC passed</span>` : "",
      s.stale   ? `<span class="pill stale">stale prompt</span>` : "",
      ...s.flags.map(f=>`<span class="pill">${f}</span>`)
    ].join("");
    return `<div class="card ${SEL.has(s.id)?"sel":""}" onclick="tog('${s.id}')">
      ${img}
      <div class="meta">
        <div class="id">${esc(s.id)}</div>
        <div class="sub">${s.day||"—"} · ${s.tier} · ${s.aspect} · ${s.renders} file(s)</div>
        <div>${pills}</div>
        <div class="sub" style="margin-top:6px">
          <a href="#" onclick="event.stopPropagation();detail('${s.id}');return false"
             style="color:var(--acc)">inspect</a></div>
      </div></div>`;
  }).join("");
  est();
}

function tog(id){ SEL.has(id)?SEL.delete(id):SEL.add(id); draw(); }
function pick(k){
  SEL.clear();
  if(k!=="none") POOL.shots.filter(s=>s[k]).forEach(s=>SEL.add(s.id));
  draw();
}
function est(){
  const n = SEL.size, u = POOL.unit||0;
  $("#est").textContent = n
    ? `${n} selected · estimate $${(n*u).toFixed(2)} at $${u.toFixed(2)}/image`
    : "nothing selected";
  $("#goBtn").disabled = !n;
}

function detail(id){
  const s = POOL.shots.find(x=>x.id===id);
  $("#did").textContent = s.id;
  $("#dstory").textContent = s.story || "—";
  $("#dprompt").textContent = s.prompt || "(dry run produced nothing)";
  $("#dimg").src = s.newest ? "/img?p="+encodeURIComponent(s.newest) : "";
  $("#dimg").style.display = s.newest ? "" : "none";
  $("#dlg").showModal();
}

async function run(dry){
  const body = {pool:$("#pool").value, model:$("#model").value,
                ids:[...SEL], budget:parseFloat($("#budget").value||"0")};
  const r = await (await fetch(dry?"/api/run/dryrun":"/api/run",
    {method:"POST",headers:{"Content-Type":"application/json"},
     body:JSON.stringify(body)})).json();
  if(!r.ok){ alert(r.error||"could not start"); return; }
  SINCE = 0; $("#log").style.display=""; $("#log").textContent="";
  poll();
}
async function poll(){
  const r = await (await fetch("/api/run?since="+SINCE)).json();
  if(r.lines.length){ $("#log").textContent += r.lines.join("\n")+"\n";
                      $("#log").scrollTop = $("#log").scrollHeight; }
  SINCE = r.total;
  if(r.running){ setTimeout(poll, 900); }
  else {
    $("#log").textContent += `\n— finished in ${r.seconds}s —\n`;
    const s = await (await fetch("/api/pools")).json(); showSpend(s.spend);
    loadPool();
  }
}

/* ---------------------------------------------------------------- publish */
async function loadPosts(){
  POSTS = (await (await fetch("/api/posts")).json()).posts || [];
  drawPosts();
}
function drawPosts(){
  $("#posts").innerHTML = POSTS.map((p,i)=>{
    const tags = (p.tags||[]).filter(Boolean);
    const over = tags.length > 5;
    const chars = (p.caption||"").length;
    return `<div class="post">
      <div>
        ${p.image?`<img src="/thumb?w=360&p=${encodeURIComponent(p.image)}">`
                 :`<div class="none" style="aspect-ratio:3/4;border-radius:6px"></div>`}
        <div class="row">
          <label class="lab" style="margin:0">crop anchor</label>
          <input size="4" value="${p.anchor??0.7}"
                 onchange="POSTS[${i}].anchor=parseFloat(this.value)">
        </div>
        <div class="row">
          <button class="ghost" onclick="exportOne(${i})">export 1080×1440</button>
        </div>
        <div class="hint" id="exp${i}">${p.export?esc(p.export):""}</div>
      </div>
      <div>
        <div class="row" style="margin-top:0">
          <input size="18" value="${esc(p.shot_id||"")}" placeholder="shot id"
                 onchange="POSTS[${i}].shot_id=this.value">
          <input size="26" value="${esc(p.image||"")}" placeholder="content/grid/....png"
                 onchange="POSTS[${i}].image=this.value;drawPosts()">
          <input size="12" value="${esc(p.scheduled||"")}" placeholder="2026-08-25"
                 onchange="POSTS[${i}].scheduled=this.value">
          <label><input type="checkbox" ${p.posted?"checked":""}
                 onchange="POSTS[${i}].posted=this.checked;drawPosts()"> posted</label>
        </div>
        <div style="margin-top:10px">
          <label class="lab">caption</label>
          <textarea rows="5"
            onchange="POSTS[${i}].caption=this.value;drawPosts()">${esc(p.caption||"")}</textarea>
          <div class="hint">${chars} characters${chars>300?" · long for a feed caption":""}</div>
        </div>
        <div class="row">
          <div style="flex:1">
            <label class="lab">hashtags (max 5)</label>
            <input style="width:100%" value="${esc(tags.join(" "))}"
              onchange="POSTS[${i}].tags=this.value.split(/\s+/).filter(Boolean);drawPosts()">
            ${over?`<div class="warn">${tags.length} tags — the cap is 5, Instagram
                    drops the rest</div>`
                  :`<div class="good">${tags.length}/5</div>`}
          </div>
          <div style="width:180px">
            <label class="lab">location</label>
            <input style="width:100%" value="${esc(p.location||"")}"
              placeholder="none" onchange="POSTS[${i}].location=this.value">
          </div>
        </div>
        <div style="margin-top:10px">
          <label class="lab">alt text</label>
          <textarea rows="3"
            onchange="POSTS[${i}].alt=this.value">${esc(p.alt||"")}</textarea>
        </div>
        <div class="row">
          <button class="ghost" onclick="POSTS.splice(${i},1);drawPosts()">remove</button>
        </div>
      </div></div>`;
  }).join("") || `<p class="hint">no posts yet</p>`;
}
function addPost(){
  POSTS.push({shot_id:"",image:"",caption:"",tags:[],location:"",alt:"",
              scheduled:"",posted:false,anchor:0.7});
  drawPosts();
}
async function savePosts(){
  const r = await (await fetch("/api/posts",{method:"POST",
    headers:{"Content-Type":"application/json"},
    body:JSON.stringify({posts:POSTS})})).json();
  $("#psave").textContent = r.ok ? `saved ${r.n}` : "save failed";
  setTimeout(()=>$("#psave").textContent="", 2500);
}
async function exportOne(i){
  const p = POSTS[i];
  if(!p.image){ alert("set the image path first"); return; }
  $("#exp"+i).textContent = "exporting…";
  const r = await (await fetch("/api/export",{method:"POST",
    headers:{"Content-Type":"application/json"},
    body:JSON.stringify({image:p.image, anchor:p.anchor??0.7, kind:"feed"})})).json();
  POSTS[i].export = r.ok ? r.path : (r.error||"failed");
  $("#exp"+i).textContent = POSTS[i].export;
}
boot();
</script></body></html>
"""


def _bind() -> tuple[ThreadingHTTPServer, int]:
    """Take the first free port from PORT upward.

    "Page not reachable" has exactly four causes and three of them are here:
    the port was already taken and the process died on OSError, the window
    closed before the traceback could be read, or the browser was pointed at a
    port nothing was listening on. A fixed port turns a five-second problem
    into a silent one."""
    last: OSError | None = None
    for p in range(PORT, PORT + 10):
        try:
            return ThreadingHTTPServer(("127.0.0.1", p), Handler), p
        except OSError as e:
            last = e
    raise last if last else OSError("no port")


def main() -> int:
    # Run from anywhere. `python console.py` typed in the wrong folder used to
    # mean "file not found"; an absolute ROOT means the only thing that has to
    # be right is the path to this file.
    if not (ROOT / "outside.py").exists():
        print(f"\n  ! outside.py is not next to console.py.")
        print(f"    console.py is at: {ROOT}")
        print(f"    It must live in the seoyeon folder, beside outside.py.\n")
        return 2

    try:
        srv, port = _bind()
    except OSError as e:
        print(f"\n  ! could not open a port: {e}")
        print(f"    Tried {PORT} to {PORT + 9}. Set another one first:")
        print(f"        set CONSOLE_PORT=9100  &&  python console.py\n")
        return 1

    url = f"http://127.0.0.1:{port}"
    print("\n  " + "-" * 52)
    print(f"  seo-yeon console   {url}")
    if port != PORT:
        print(f"  (port {PORT} was busy, took {port} instead)")
    print(f"  project            {ROOT}")
    print(f"  python             {sys.version.split()[0]}")
    print("  loopback only - nothing off this machine can reach it")
    print("  ctrl-c to stop")
    print("  " + "-" * 52 + "\n")

    try:
        import webbrowser
        webbrowser.open(url)
    except Exception:                                        # noqa: BLE001
        print(f"  (could not open a browser - go to {url} yourself)\n")

    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\n  stopped")
    return 0


if __name__ == "__main__":
    try:
        code = main()
    except Exception:                                        # noqa: BLE001
        # A double-clicked .py on Windows closes its window the instant it
        # raises, which is how a real traceback becomes "page not reachable".
        # Print it and hold the window open.
        import traceback
        traceback.print_exc()
        code = 1
    if code:
        try:
            input("\n  press Enter to close ")
        except EOFError:
            pass
    sys.exit(code)
