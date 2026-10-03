"""
personas/seoyeon/qc_gate.py — Deterministic pre-flight Quality Control gate.
Used by Sentry and the pipeline runner to validate files, dimensions, tiers,
and caption syntax before/alongside vision inspection.
Non-spending, zero-API, runs completely locally on Windows.
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional

try:
    from PIL import Image
except ImportError:
    Image = None

# Forbidden sales & marketing keywords (character voice violation)
SALES_BUZZWORDS = [
    "unlock",
    "exclusive",
    "link in bio",
    "links in bio",
    "check bio",
    "you won't believe",
    "subscribe now",
    "free trial",
    "limited time",
    "dm me for",
    "buy now",
    "check out my",
]

# Age-baiting / policy violation terms
AGE_BAITING = [
    "teen",
    "barely legal",
    "just turned 18",
    "schoolgirl",
]

# Canonical tags required/expected on IG
IG_CANONICAL_TAGS = ["#seongsu", "#seoul", "#daily", "#filmphoto", "#everyday"]


def validate_image(image_path: str, expected_ratio: float = 0.75, min_width: int = 864) -> Dict[str, Any]:
    """Validate image file existence, format, dimensions and aspect ratio."""
    res = {"path": image_path, "passed": True, "errors": [], "warnings": [], "metadata": {}}
    
    if not os.path.isfile(image_path):
        res["passed"] = False
        res["errors"].append(f"Image file does not exist: {image_path}")
        return res

    size_bytes = os.path.getsize(image_path)
    res["metadata"]["size_bytes"] = size_bytes
    if size_bytes < 10000:
        res["passed"] = False
        res["errors"].append(f"Image file suspiciously small ({size_bytes} bytes), likely corrupt")
        return res

    if Image is None:
        res["warnings"].append("Pillow (PIL) not installed; skipped pixel dimension checks")
        return res

    try:
        with Image.open(image_path) as img:
            w, h = img.size
            res["metadata"]["width"] = w
            res["metadata"]["height"] = h
            res["metadata"]["format"] = img.format
            res["metadata"]["mode"] = img.mode

            if img.format not in ("PNG", "JPEG", "WEBP"):
                res["passed"] = False
                res["errors"].append(f"Disallowed image format: {img.format} (must be PNG, JPEG, or WEBP)")

            if w < min_width:
                res["passed"] = False
                res["errors"].append(f"Image width {w}px is below the {min_width}px minimum floor")

            # Check 3:4 ratio (0.75) with 5% tolerance
            actual_ratio = w / h
            res["metadata"]["aspect_ratio"] = round(actual_ratio, 3)
            if abs(actual_ratio - expected_ratio) > 0.06 and abs(actual_ratio - 1.0) > 0.05:
                # allow 3:4 and 1:1, warn otherwise
                res["warnings"].append(f"Aspect ratio {actual_ratio:.3f} deviates from expected 3:4 (0.75)")

    except Exception as e:
        res["passed"] = False
        res["errors"].append(f"Failed to decode image file: {e}")

    return res


def validate_caption(
    caption_text: str,
    tier: int = 1,
    lane: str = "instagram"
) -> Dict[str, Any]:
    """Validate caption register, forbidden words, age rules, and CTA links."""
    res = {"passed": True, "errors": [], "warnings": [], "patches": []}

    if not caption_text or not caption_text.strip():
        res["passed"] = False
        res["errors"].append("Caption is empty")
        return res

    lower_text = caption_text.lower()

    # 1. No exclamation marks
    if "!" in caption_text:
        res["passed"] = False
        res["errors"].append("Exclamation mark found. Her voice uses full stops only, never '!'")
        res["patches"].append("Replace '!' with '.'")

    # 2. Sales / hype jargon check
    for word in SALES_BUZZWORDS:
        if re.search(r"\b" + re.escape(word) + r"\b", lower_text):
            res["passed"] = False
            res["errors"].append(f"Forbidden sales language detected: '{word}'")

    # 3. Age safety check (25 until 23 Oct 2026, never 26 in copy, never age-baiting)
    for term in AGE_BAITING:
        if term in lower_text:
            res["passed"] = False
            res["errors"].append(f"Age-baiting / policy violation term detected: '{term}'")

    if re.search(r"\b26\s*(years old|yo|age)\b", lower_text):
        res["passed"] = False
        res["errors"].append("Age stated as 26 in copy. Canon age is 25 until 23 October.")

    # 4. Check case style (should be mostly lowercase, full stops)
    lines = [l.strip() for l in caption_text.splitlines() if l.strip() and not l.startswith("#")]
    for line in lines:
        if line[0].isupper() and not line.startswith("http"):
            res["warnings"].append(f"Line starts with uppercase letter: '{line[:30]}...'. Preferred: lowercase.")

    # 5. Lane-specific checks
    if lane == "instagram":
        # Tier 1 check
        if tier != 1:
            res["passed"] = False
            res["errors"].append(f"Instagram posts must be Tier 1. Declared tier: {tier}")
        # CTA check: no hard sell or direct paywall links in IG caption body
        if "fanvue.com" in lower_text or "onlyfans" in lower_text:
            res["passed"] = False
            res["errors"].append("Direct adult links forbidden in IG caption. Traffic leaves only via bio link.")
        # Check canonical 5 hashtags
        missing_tags = [tag for tag in IG_CANONICAL_TAGS if tag not in lower_text]
        if missing_tags:
            res["warnings"].append(f"Missing canonical IG hashtag(s): {', '.join(missing_tags)}")
            res["patches"].append(f"Append tags: {' '.join(IG_CANONICAL_TAGS)}")

    elif lane in ("bluesky", "fanvue"):
        if lane == "bluesky":
            # Bluesky teasers are tier 2
            if tier != 2:
                res["warnings"].append(f"Bluesky public teasers should be Tier 2. Declared tier: {tier}")
            # Ensure CTA link format
            if "?c=fv-4" not in caption_text and "https://www.fanvue.com/syeon.hn" in caption_text:
                res["warnings"].append("Fanvue link missing tracking code '?c=fv-4'")

    return res


def resolve_path(rel_path: str, root_dir: Path, handoff_dir: Optional[Path] = None) -> Path:
    """Resolve a relative path against candidate directories."""
    p = Path(rel_path)
    if p.is_absolute():
        return p
    
    # 1. Check relative to root_dir
    cand1 = root_dir / p
    if cand1.exists():
        return cand1

    # 2. Check relative to personas/seoyeon/
    cand2 = root_dir / "personas" / "seoyeon" / p
    if cand2.exists():
        return cand2

    # 3. Check relative to handoff_dir if provided
    if handoff_dir:
        cand3 = handoff_dir / p
        if cand3.exists():
            return cand3

    return cand1


def validate_handoff_entry(entry: Dict[str, Any], root_dir: Path, handoff_dir: Optional[Path] = None) -> Dict[str, Any]:
    """Validate a single post entry from a handoff payload."""
    entry_id = entry.get("id", "unknown")
    tier = entry.get("tier", 1)
    lanes = entry.get("lanes", ["instagram"])
    primary_lane = lanes[0] if lanes else "instagram"

    report = {
        "id": entry_id,
        "tier": tier,
        "lanes": lanes,
        "passed": True,
        "image_qc": None,
        "caption_qc": None,
    }

    # Validate media file
    media_rel = entry.get("media_file")
    min_w = 1080 if primary_lane == "instagram" else 864
    if media_rel:
        media_path = resolve_path(media_rel, root_dir, handoff_dir)
        img_qc = validate_image(str(media_path), min_width=min_w)
        report["image_qc"] = img_qc
        if not img_qc["passed"]:
            report["passed"] = False

    # Validate gallery files if present
    gallery_files = entry.get("fanvue_gallery_files") or entry.get("gallery_files") or []
    if gallery_files:
        report["gallery_qc"] = []
        for g_file in gallery_files:
            g_path = resolve_path(g_file, root_dir, handoff_dir)
            g_qc = validate_image(str(g_path), min_width=min_w)
            report["gallery_qc"].append(g_qc)
            if not g_qc["passed"]:
                report["passed"] = False

    # Validate caption file or text
    caption_text = None
    caption_rel = entry.get("caption_file")
    if caption_rel:
        cap_path = resolve_path(caption_rel, root_dir, handoff_dir)
        if cap_path.is_file():
            try:
                caption_text = cap_path.read_text(encoding="utf-8")
            except Exception as e:
                report["passed"] = False
                report["caption_qc"] = {"passed": False, "errors": [f"Cannot read caption file: {e}"]}
        else:
            report["passed"] = False
            report["caption_qc"] = {"passed": False, "errors": [f"Caption file does not exist: {cap_path}"]}

    if caption_text is None and "caption" in entry:
        caption_text = entry["caption"]
    if caption_text is None and "main_text" in entry:
        caption_text = entry["main_text"]

    if caption_text:
        cap_qc = validate_caption(caption_text, tier=tier, lane=primary_lane)
        report["caption_qc"] = cap_qc
        if not cap_qc["passed"]:
            report["passed"] = False

    return report


def audit_handoff_file(handoff_path: str, root_dir: Optional[str] = None) -> Dict[str, Any]:
    """Audit an entire handoff JSON file."""
    if root_dir is None:
        # Defaults to repo root
        root = Path(__file__).resolve().parent.parent.parent
    else:
        root = Path(root_dir)

    hp = Path(handoff_path)
    if not hp.is_file():
        return {"passed": False, "error": f"Handoff file not found: {handoff_path}"}

    handoff_dir = hp.resolve().parent

    with open(hp, "r", encoding="utf-8") as f:
        data = json.load(f)

    entries = data.get("entries", data.get("drops", data.get("items", [])))
    if isinstance(data, list):
        entries = data
    elif isinstance(data, dict) and not entries and ("id" in data or "media_file" in data or "fanvue_gallery_files" in data):
        entries = [data]

    results = []
    all_passed = True

    for item in entries:
        res = validate_handoff_entry(item, root, handoff_dir)
        if not res["passed"]:
            all_passed = False
        results.append(res)

    return {
        "passed": all_passed,
        "total_entries": len(entries),
        "failed_entries": sum(1 for r in results if not r["passed"]),
        "results": results
    }


def main():
    parser = argparse.ArgumentParser(description="QC Gate deterministic pre-flight checks")
    parser.add_argument("--handoff", type=str, help="Path to handoff.json to audit")
    parser.add_argument("--media", type=str, help="Single image file path to validate")
    parser.add_argument("--caption", type=str, help="Caption text or path to caption txt file")
    parser.add_argument("--tier", type=int, default=1, help="Content tier (1, 2, or 3)")
    parser.add_argument("--lane", type=str, default="instagram", help="instagram, bluesky, or fanvue")
    parser.add_argument("--test", action="store_true", help="Run self-test on test fixtures")
    args = parser.parse_args()

    if args.test:
        print("[QC-GATE] Running self-tests...")
        # 1. Test good caption
        good_cap = "17 degrees this morning and the walk to the station is cold.\n\nfirst time in four months.\n#seongsu #seoul"
        qc1 = validate_caption(good_cap, tier=1, lane="instagram")
        assert qc1["passed"], f"Expected pass, got: {qc1}"

        # 2. Test bad caption with exclamation and sales jargon
        bad_cap = "Unlock my exclusive morning routine! Link in bio!"
        qc2 = validate_caption(bad_cap, tier=1, lane="instagram")
        assert not qc2["passed"], "Expected failure on sales/exclamation"
        assert len(qc2["errors"]) >= 2

        print("[QC-GATE] All self-tests passed successfully.")
        sys.exit(0)

    if args.handoff:
        res = audit_handoff_file(args.handoff)
        print(json.dumps(res, indent=2))
        sys.exit(0 if res["passed"] else 1)

    if args.media:
        res = validate_image(args.media)
        print(json.dumps(res, indent=2))
        sys.exit(0 if res["passed"] else 1)

    if args.caption:
        text = args.caption
        if os.path.isfile(text):
            with open(text, "r", encoding="utf-8") as f:
                text = f.read()
        res = validate_caption(text, tier=args.tier, lane=args.lane)
        print(json.dumps(res, indent=2))
        sys.exit(0 if res["passed"] else 1)

    parser.print_help()


if __name__ == "__main__":
    main()
