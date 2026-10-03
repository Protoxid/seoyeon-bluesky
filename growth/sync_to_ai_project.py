#!/usr/bin/env python3
"""
sync_to_ai_project.py — Comprehensive sync of all new/modified files
from 'c:/AI-Project - Copia' to 'c:/AI-Project'.
"""
import os
import pathlib
import shutil

SRC = pathlib.Path(r"c:\AI-Project - Copia")
DST = pathlib.Path(r"c:\AI-Project")

def sync_file(rel_path: str):
    sf = SRC / rel_path
    df = DST / rel_path
    if not sf.exists():
        print(f"Skipping non-existent: {rel_path}")
        return
    df.parent.mkdir(parents=True, exist_ok=True)
    try:
        shutil.copy2(sf, df)
        print(f"Synced file: {rel_path}")
    except Exception as e:
        print(f"Warning: could not sync file {rel_path}: {e}")

def sync_dir(rel_path: str):
    sdir = SRC / rel_path
    ddir = DST / rel_path
    if not sdir.exists():
        return
    ddir.mkdir(parents=True, exist_ok=True)
    count = 0
    for root, dirs, files in os.walk(sdir):
        if "__pycache__" in root:
            continue
        for f in files:
            s_file = pathlib.Path(root) / f
            r_file = s_file.relative_to(sdir)
            d_file = ddir / r_file
            d_file.parent.mkdir(parents=True, exist_ok=True)
            try:
                shutil.copy2(s_file, d_file)
                count += 1
            except Exception as e:
                print(f"Warning: could not sync {r_file}: {e}")
    print(f"Synced directory {rel_path} ({count} files)")

def main():
    print(f"=== Syncing from {SRC} to {DST} ===")

    # 1. Growth folder
    sync_dir("growth")

    # 2. ComfyUI workflows
    sync_dir("comfyui")

    # 3. Content outputs (fanvue and exclusive)
    sync_dir("personas/seoyeon/content/fanvue")
    sync_dir("personas/seoyeon/content/exclusive")

    # 4. Caps, clips, _prep, _trash
    sync_dir("personas/seoyeon/caps")
    sync_dir("personas/seoyeon/clips")
    sync_dir("personas/seoyeon/_prep")
    sync_dir("personas/seoyeon/_trash")

    # 5. Wiki documentation
    sync_dir("personas/seoyeon/wiki")

    # 6. Specific pipeline & shot scripts
    scripts = [
        "personas/seoyeon/exclusive_shots.py",
        "personas/seoyeon/fanvue_shots.py",
        "personas/seoyeon/build_reel_c_7am.py",
        "personas/seoyeon/burn_r4_text.py",
        "personas/seoyeon/make_reel_rA.py",
        "personas/seoyeon/run_comfy_exclusive.py",
        "personas/seoyeon/ffbin.py",
        "personas/seoyeon/grid_shots.py",
        "personas/seoyeon/kie_api.py",
        "personas/seoyeon/make_reel_text.py",
        "personas/seoyeon/make_voice.py",
        "personas/seoyeon/publish_queue.py",
        "personas/seoyeon/week2_shots.py",
        "personas/seoyeon/weekly_prep.py",
        "personas/seoyeon/audit_video.py",
    ]
    for s in scripts:
        sync_file(s)

    # 7. Merge console.py (add PYTHONUTF8=1)
    console_p = DST / "personas/seoyeon/console.py"
    if console_p.exists():
        c_text = console_p.read_text(encoding="utf-8")
        if "PYTHONUTF8" not in c_text:
            c_text = c_text.replace(
                '            self.proc = subprocess.Popen(\n                cmd, cwd=str(ROOT), stdout=subprocess.PIPE,',
                '            env = {**os.environ, "PYTHONUTF8": "1"}\n            self.proc = subprocess.Popen(\n                cmd, cwd=str(ROOT), stdout=subprocess.PIPE,',
            )
            c_text = c_text.replace(
                '                encoding="utf-8", errors="replace")',
                '                encoding="utf-8", errors="replace", env=env)',
            )
            c_text = c_text.replace(
                'cmd = [sys.executable, "-u", "outside.py", *flags, "--all",',
                'cmd = [sys.executable, "-Xutf8", "-u", "outside.py", *flags, "--all",',
            )
            console_p.write_text(c_text, encoding="utf-8")
            print("Merged UTF-8 hardening into c:/AI-Project/personas/seoyeon/console.py")

    # 8. Merge outside.py (UTF-8 reconfigure + exclusive_shots support while preserving lora_shots)
    outside_p = DST / "personas/seoyeon/outside.py"
    if outside_p.exists():
        o_text = outside_p.read_text(encoding="utf-8")
        if "reconfigure" not in o_text:
            marker = "from concurrent.futures import ThreadPoolExecutor, as_completed"
            replacement = (
                "from concurrent.futures import ThreadPoolExecutor, as_completed\n\n"
                "if hasattr(sys.stdout, 'reconfigure'):\n"
                "    sys.stdout.reconfigure(encoding='utf-8', errors='replace')\n"
                "if hasattr(sys.stderr, 'reconfigure'):\n"
                "    sys.stderr.reconfigure(encoding='utf-8', errors='replace')"
            )
            o_text = o_text.replace(marker, replacement, 1)

        if "exclusive_shots" not in o_text:
            marker = "from outside_shots import SHOTS"
            addition = (
                "from outside_shots import SHOTS\n"
                "# The Exclusive / Subscriber set — private, intimate, SFW moments (Plan B).\n"
                "try:\n"
                "    from exclusive_shots import SHOTS as EX_SHOTS\n"
                "except Exception:\n"
                "    EX_SHOTS = []"
            )
            o_text = o_text.replace(marker, addition, 1)

        if "--exclusive" not in o_text:
            o_text = o_text.replace(
                'ap.add_argument("--fanvue", action="store_true",',
                'ap.add_argument("--exclusive", action="store_true", help="run the exclusive_shots set into content/exclusive")\n    ap.add_argument("--fanvue", action="store_true",',
                1
            )

        if "EX_SHOTS if a.exclusive" not in o_text:
            o_text = o_text.replace(
                'pool = (FV_SHOTS if a.fanvue else RF_SHOTS if a.reel_frames',
                'pool = (EX_SHOTS if (getattr(a, "exclusive", False) or a.fanvue) else RF_SHOTS if a.reel_frames',
                1
            )
            o_text = o_text.replace(
                'if a.fanvue:\n        globals()["OUT"] = ROOT / "content" / "fanvue"',
                'if getattr(a, "exclusive", False) or a.fanvue:\n        globals()["OUT"] = ROOT / "content" / ("exclusive" if getattr(a, "exclusive", False) else "fanvue")',
                1
            )

        outside_p.write_text(o_text, encoding="utf-8")
        print("Merged exclusive and UTF-8 features into c:/AI-Project/personas/seoyeon/outside.py")

    print("\n=== All items successfully moved/synced to c:/AI-Project! ===")

if __name__ == "__main__":
    main()
