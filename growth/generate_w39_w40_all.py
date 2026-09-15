#!/usr/bin/env python3
"""
generate_w39_w40_all.py — Autonomous multi-lane generation runner for Weeks 39 and 40.

Generates:
1. W39 Instagram (7 shots, gpt-image-2-5-sunburst-image-to-image, 1K tier)
2. W39 Bluesky & Fanvue drops (7 teasers + 14 companion reveals = 21 shots, Seedream 5 Pro, 1K tier)
3. W40 Instagram (7 shots, gpt-image-2-5-sunburst-image-to-image, 1K tier)
4. W40 Bluesky & Fanvue drops (7 teasers + 14 companion reveals = 21 shots, Seedream 5 Pro, 1K tier)

Total: 56 canon images.
All generated at 1K resolution tier with strict anti-defect prompt & plate invariants.
"""
from __future__ import annotations

import argparse
import os
import pathlib
import sys
import time

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)

ROOT_DIR = pathlib.Path(__file__).resolve().parent.parent
GROWTH_DIR = ROOT_DIR / "growth"
PERSONA_DIR = ROOT_DIR / "personas" / "seoyeon"

sys.path.insert(0, str(PERSONA_DIR))
sys.path.insert(0, str(GROWTH_DIR))

from kie_api import Kie, load_key
import generate_w39_ig
import generate_w39_drops
import generate_w40_ig
import generate_w40_drops

LOG_FILE = GROWTH_DIR / "schedule_assets" / "generation_w39_w40.log"


def log(msg: str):
    timestamp = time.strftime("[%Y-%m-%d %H:%M:%S]")
    line = f"{timestamp} {msg}"
    print(line, flush=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def run_all(force: bool = False, skip_ig: bool = False, skip_adult: bool = False):
    load_key(PERSONA_DIR)
    key = os.environ.get("KIE_API_KEY", "")
    if not key:
        sys.exit("Error: KIE_API_KEY missing.")

    kie = Kie(key)
    cred = kie.credit()
    log(f"=== Starting Autonomous Generation for W39 & W40 ===")
    log(f"Kie Starting Credits: {cred}")

    total_attempted = 0
    total_rendered = 0
    total_skipped = 0
    total_failed = 0

    # 1. Week 39 Instagram (7 shots)
    if not skip_ig:
        log("\n--- [1/4] Processing Week 39 Instagram (Tier 1 SFW, gpt-image-2.5) ---")
        face_url = kie.upload(generate_w39_ig.MASTER_A1)
        plate_urls = {}
        for s in generate_w39_ig.SHOTS:
            if s["plate"]:
                p_path = generate_w39_ig.PLATES / s["plate"]
                if str(p_path) not in plate_urls:
                    plate_urls[str(p_path)] = kie.upload(str(p_path))

        for s in generate_w39_ig.SHOTS:
            total_attempted += 1
            sid = s["id"]
            dest = generate_w39_ig.OUT_DIR / f"{sid}.png"
            if dest.exists() and not force:
                log(f"  [SKIP] IG W39 {sid} already exists ({dest.stat().st_size // 1024} KB)")
                total_skipped += 1
                continue

            refs = []
            if s["plate"]:
                refs.append(plate_urls[str(generate_w39_ig.PLATES / s["plate"])])
            if s["has_person"]:
                refs.append(face_url)

            model = "gpt-image-2-5-sunburst-image-to-image" if refs else "gpt-image-2-text-to-image"
            log(f"  --> Rendering IG W39: {sid} (Model: {model}, Refs: {len(refs)})...")
            t0 = time.time()
            try:
                urls = kie.generate(
                    prompt=s["prompt"],
                    aspect="3:4",
                    image_urls=refs if refs else None,
                    model=model,
                    tier="1k",
                )
                if urls:
                    n = kie.download(urls[0], dest)
                    elapsed = time.time() - t0
                    log(f"  ✓ [SUCCESS] Rendered {dest.name} ({n // 1024} KB in {elapsed:.1f}s)")
                    total_rendered += 1
                else:
                    log(f"  ✗ [FAILED] {sid}: No URL returned")
                    total_failed += 1
            except Exception as e:
                log(f"  ✗ [ERROR] {sid}: {e}")
                total_failed += 1

    # 2. Week 39 Bluesky & Fanvue (21 shots)
    if not skip_adult:
        log("\n--- [2/4] Processing Week 39 Bluesky & Fanvue Drops (Seedream 5 Pro) ---")
        a1_url = kie.upload(generate_w39_drops.MASTER_A1.resolve())
        c5_url = kie.upload(generate_w39_drops.MASTER_C5.resolve()) if generate_w39_drops.MASTER_C5.exists() else None
        tat_url = kie.upload(generate_w39_drops.MASTER_TATTOO.resolve()) if generate_w39_drops.MASTER_TATTOO.exists() else None
        adult_refs = [a1_url]
        if c5_url:
            adult_refs.append(c5_url)
        if tat_url:
            adult_refs.append(tat_url)

        for d_key, drop in generate_w39_drops.W39_DROPS.items():
            drop_id = drop["id"]
            # Teaser
            total_attempted += 1
            teaser_dest = ROOT_DIR / drop["media_file"]
            teaser_dest.parent.mkdir(parents=True, exist_ok=True)
            if teaser_dest.exists() and not force:
                log(f"  [SKIP] Teaser W39 {teaser_dest.name} exists")
                total_skipped += 1
            else:
                refs = [a1_url] if drop.get("teaser_exclude_body_ref", False) else adult_refs
                log(f"  --> Rendering W39 Teaser: {drop_id} ({len(refs)} refs)...")
                t0 = time.time()
                try:
                    urls = kie.generate(
                        prompt=drop["teaser_prompt"],
                        aspect="3:4",
                        tier="1k",
                        image_urls=refs,
                        model="seedream/5-pro-image-to-image",
                    )
                    if urls:
                        n = kie.download(urls[0], teaser_dest)
                        log(f"  ✓ [SUCCESS] Teaser {teaser_dest.name} ({n // 1024} KB in {time.time() - t0:.1f}s)")
                        total_rendered += 1
                    else:
                        log(f"  ✗ [FAILED] Teaser {drop_id}: No URL returned")
                        total_failed += 1
                except Exception as e:
                    log(f"  ✗ [ERROR] Teaser {drop_id}: {e}")
                    total_failed += 1

            # Companion shots
            drop_dir = generate_w39_drops.SETS_DIR / drop_id
            drop_dir.mkdir(parents=True, exist_ok=True)
            for shot in drop["shots"]:
                total_attempted += 1
                s_dest = drop_dir / shot["filename"]
                if s_dest.exists() and not force:
                    log(f"  [SKIP] Companion W39 {drop_id}/{shot['filename']} exists")
                    total_skipped += 1
                    continue
                refs = [a1_url] if shot.get("exclude_body_ref", False) else adult_refs
                log(f"  --> Rendering W39 Companion: {drop_id}/{shot['filename']} ({len(refs)} refs)...")
                t0 = time.time()
                try:
                    urls = kie.generate(
                        prompt=shot["prompt"],
                        aspect="3:4",
                        tier="1k",
                        image_urls=refs,
                        model="seedream/5-pro-image-to-image",
                    )
                    if urls:
                        n = kie.download(urls[0], s_dest)
                        log(f"  ✓ [SUCCESS] Companion {s_dest.name} ({n // 1024} KB in {time.time() - t0:.1f}s)")
                        total_rendered += 1
                    else:
                        log(f"  ✗ [FAILED] Companion {drop_id}/{shot['filename']}: No URL")
                        total_failed += 1
                except Exception as e:
                    log(f"  ✗ [ERROR] Companion {drop_id}/{shot['filename']}: {e}")
                    total_failed += 1

    # 3. Week 40 Instagram (7 shots)
    if not skip_ig:
        log("\n--- [3/4] Processing Week 40 Instagram (Tier 1 SFW, gpt-image-2.5) ---")
        face_url = kie.upload(generate_w40_ig.MASTER_A1)
        plate_urls = {}
        for s in generate_w40_ig.SHOTS:
            if s["plate"]:
                p_path = generate_w40_ig.PLATES / s["plate"]
                if str(p_path) not in plate_urls:
                    plate_urls[str(p_path)] = kie.upload(str(p_path))

        for s in generate_w40_ig.SHOTS:
            total_attempted += 1
            sid = s["id"]
            dest = generate_w40_ig.OUT_DIR / f"{sid}.png"
            if dest.exists() and not force:
                log(f"  [SKIP] IG W40 {sid} already exists ({dest.stat().st_size // 1024} KB)")
                total_skipped += 1
                continue

            refs = []
            if s["plate"]:
                refs.append(plate_urls[str(generate_w40_ig.PLATES / s["plate"])])
            if s["has_person"]:
                refs.append(face_url)

            model = "gpt-image-2-5-sunburst-image-to-image" if refs else "gpt-image-2-text-to-image"
            log(f"  --> Rendering IG W40: {sid} (Model: {model}, Refs: {len(refs)})...")
            t0 = time.time()
            try:
                urls = kie.generate(
                    prompt=s["prompt"],
                    aspect="3:4",
                    image_urls=refs if refs else None,
                    model=model,
                    tier="1k",
                )
                if urls:
                    n = kie.download(urls[0], dest)
                    elapsed = time.time() - t0
                    log(f"  ✓ [SUCCESS] Rendered {dest.name} ({n // 1024} KB in {elapsed:.1f}s)")
                    total_rendered += 1
                else:
                    log(f"  ✗ [FAILED] {sid}: No URL returned")
                    total_failed += 1
            except Exception as e:
                log(f"  ✗ [ERROR] {sid}: {e}")
                total_failed += 1

    # 4. Week 40 Bluesky & Fanvue (21 shots)
    if not skip_adult:
        log("\n--- [4/4] Processing Week 40 Bluesky & Fanvue Drops (Seedream 5 Pro) ---")
        a1_url = kie.upload(generate_w40_drops.MASTER_A1.resolve())
        c5_url = kie.upload(generate_w40_drops.MASTER_C5.resolve()) if generate_w40_drops.MASTER_C5.exists() else None
        tat_url = kie.upload(generate_w40_drops.MASTER_TATTOO.resolve()) if generate_w40_drops.MASTER_TATTOO.exists() else None
        adult_refs = [a1_url]
        if c5_url:
            adult_refs.append(c5_url)
        if tat_url:
            adult_refs.append(tat_url)

        for d_key, drop in generate_w40_drops.W40_DROPS.items():
            drop_id = drop["id"]
            # Teaser
            total_attempted += 1
            teaser_dest = ROOT_DIR / drop["media_file"]
            teaser_dest.parent.mkdir(parents=True, exist_ok=True)
            if teaser_dest.exists() and not force:
                log(f"  [SKIP] Teaser W40 {teaser_dest.name} exists")
                total_skipped += 1
            else:
                refs = [a1_url] if drop.get("teaser_exclude_body_ref", False) else adult_refs
                log(f"  --> Rendering W40 Teaser: {drop_id} ({len(refs)} refs)...")
                t0 = time.time()
                try:
                    urls = kie.generate(
                        prompt=drop["teaser_prompt"],
                        aspect="3:4",
                        tier="1k",
                        image_urls=refs,
                        model="seedream/5-pro-image-to-image",
                    )
                    if urls:
                        n = kie.download(urls[0], teaser_dest)
                        log(f"  ✓ [SUCCESS] Teaser {teaser_dest.name} ({n // 1024} KB in {time.time() - t0:.1f}s)")
                        total_rendered += 1
                    else:
                        log(f"  ✗ [FAILED] Teaser {drop_id}: No URL returned")
                        total_failed += 1
                except Exception as e:
                    log(f"  ✗ [ERROR] Teaser {drop_id}: {e}")
                    total_failed += 1

            # Companion shots
            drop_dir = generate_w40_drops.SETS_DIR / drop_id
            drop_dir.mkdir(parents=True, exist_ok=True)
            for shot in drop["shots"]:
                total_attempted += 1
                s_dest = drop_dir / shot["filename"]
                if s_dest.exists() and not force:
                    log(f"  [SKIP] Companion W40 {drop_id}/{shot['filename']} exists")
                    total_skipped += 1
                    continue
                refs = [a1_url] if shot.get("exclude_body_ref", False) else adult_refs
                log(f"  --> Rendering W40 Companion: {drop_id}/{shot['filename']} ({len(refs)} refs)...")
                t0 = time.time()
                try:
                    urls = kie.generate(
                        prompt=shot["prompt"],
                        aspect="3:4",
                        tier="1k",
                        image_urls=refs,
                        model="seedream/5-pro-image-to-image",
                    )
                    if urls:
                        n = kie.download(urls[0], s_dest)
                        log(f"  ✓ [SUCCESS] Companion {s_dest.name} ({n // 1024} KB in {time.time() - t0:.1f}s)")
                        total_rendered += 1
                    else:
                        log(f"  ✗ [FAILED] Companion {drop_id}/{shot['filename']}: No URL")
                        total_failed += 1
                except Exception as e:
                    log(f"  ✗ [ERROR] Companion {drop_id}/{shot['filename']}: {e}")
                    total_failed += 1

    end_cred = kie.credit()
    log("\n" + "=" * 80)
    log(f"  GENERATION RUN COMPLETE")
    log(f"  Total Attempted: {total_attempted}")
    log(f"  Total Rendered:  {total_rendered}")
    log(f"  Total Skipped:   {total_skipped}")
    log(f"  Total Failed:    {total_failed}")
    log(f"  Ending Kie Credits: {end_cred}")
    log("=" * 80)


def main():
    parser = argparse.ArgumentParser(description="Master multi-lane generation runner for W39 & W40")
    parser.add_argument("--force", action="store_true", help="Force overwrite of existing files")
    parser.add_argument("--skip-ig", action="store_true", help="Skip Instagram lanes")
    parser.add_argument("--skip-adult", action="store_true", help="Skip Bluesky/Fanvue adult companion lanes")
    args = parser.parse_args()

    run_all(force=args.force, skip_ig=args.skip_ig, skip_adult=args.skip_adult)


if __name__ == "__main__":
    main()
