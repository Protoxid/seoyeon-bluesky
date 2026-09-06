#!/usr/bin/env python3
"""
publish_prep.py — final export before upload.

Instagram re-compresses every image and offers no quality toggle, so the only
lever is handing it a file that needs the least work. Verified targets:
    feed    1080 x 1440  (3:4)  <- matches what we generate, crops nowhere
    story   1080 x 1920  (9:16)
    square  1080 x 1080  (1:1)   profile picture
    sRGB, JPEG, under 3.6 MB, quality 85-95

Uploading larger than 1080 wide does not help — Instagram downscales it and
compresses the result, which is worse than downscaling cleanly ourselves.

    python publish_prep.py content/outside --kind feed
    python publish_prep.py content/outside --kind story
    python publish_prep.py heroes/profile.png --kind square
"""
from __future__ import annotations
import argparse, pathlib, sys
from PIL import Image, ImageCms

# Instagram moved the profile grid to 3:4 in January 2025 and added native 3:4
# photo support in May 2025. The feed now accepts 1.91:1 through 3:4, and the
# grid crops EVERYTHING to 3:4. So for a bank generated at 3:4:
#   3:4 uploaded -> zero crop in the feed AND zero crop in the grid
#   4:5 uploaded -> thin strips lost from both sides in the grid, for nothing
# 3:4 is also taller in feed, so it takes more screen. Do not export 4:5.
SIZES = {"feed": (1080, 1440), "story": (1080, 1920), "square": (1080, 1080),
         "feed45": (1080, 1350)}     # only if a shot was framed for 4:5
MAX_BYTES = 3.6 * 1024 * 1024


def to_srgb(im: Image.Image) -> Image.Image:
    """Convert an embedded profile to sRGB. Instagram assumes sRGB and does
    not read profiles, so anything else shifts colour on upload."""
    icc = im.info.get("icc_profile")
    if icc:
        try:
            src = ImageCms.ImageCmsProfile(__import__("io").BytesIO(icc))
            im = ImageCms.profileToProfile(im, src, ImageCms.createProfile("sRGB"),
                                           outputMode="RGB")
        except Exception:
            im = im.convert("RGB")
    return im.convert("RGB")


def fit(im: Image.Image, target: tuple[int, int],
        anchor: float = 0.70) -> Image.Image:
    """Cover-crop to the target ratio, then resize.

    Horizontally always centred. Vertically, `anchor` is the fraction of the
    loss taken off the TOP: 0.70 by default because headroom is the expendable
    part and hands and feet are not. Use 0.5 for a centred crop, or lower when
    the subject sits high in the frame — a mirror selfie loses its head at
    0.70."""
    tw, th = target
    tr, ir = tw / th, im.width / im.height
    if ir > tr:                      # too wide: trim the sides
        w = round(im.height * tr)
        left = (im.width - w) // 2
        im = im.crop((left, 0, left + w, im.height))
    elif ir < tr:                    # too tall: trim mostly off the top
        h = round(im.width / tr)
        top = round((im.height - h) * anchor)
        im = im.crop((0, top, im.width, top + h))
    return im.resize(target, Image.LANCZOS)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("target", help="a PNG, or a folder of them")
    ap.add_argument("--kind", choices=list(SIZES) + ["auto"], default="auto",
                    help="auto routes each file by its own aspect: 3:4 and "
                         "anything near it -> feed, tall -> story, square -> "
                         "square. Force one target only if you mean to crop.")
    ap.add_argument("--quality", type=int, default=92)
    ap.add_argument("--anchor", type=float, default=0.70,
                    help="fraction of the vertical crop taken off the top. "
                         "0.70 default (headroom goes first), 0.5 centred, "
                         "0.2 when the subject sits high in frame")
    ap.add_argument("--out", default="publish")
    a = ap.parse_args()

    root = pathlib.Path(__file__).parent
    t = root / a.target if not pathlib.Path(a.target).is_absolute() else pathlib.Path(a.target)
    files = [t] if t.is_file() else sorted(
        f for f in t.rglob("*.png")
        if not f.name.endswith(".orig.png") and "superseded" not in f.name)
    if not files:
        sys.exit(f"no PNGs under {t}")

    def route(im):
        """Pick the target from the source's own ratio, so nothing is cropped
        that does not need to be. Ratios are w/h: 1:1 = 1.00, 3:4 = 0.75,
        9:16 = 0.5625."""
        r = im.width / im.height
        if r > 0.92:
            return "square"
        if r < 0.65:
            return "story"
        return "feed"

    skipped = []
    for f in files:
        src = Image.open(f)
        # Upscaling past the source invents detail, and Instagram then
        # compresses the invention. Refuse and name the file instead.
        kind = route(src) if a.kind == "auto" else a.kind
        size = SIZES[kind]
        if src.width < size[0]:
            skipped.append((f.name, src.size, size[0]))
            continue
        outdir = root / a.out / kind
        outdir.mkdir(parents=True, exist_ok=True)
        # keep the source folder in the name so nothing collides
        tag = f.parent.name if f.parent.name not in ("content", "heroes") else ""
        stem = f"{tag}__{f.stem}" if tag else f.stem
        im = fit(to_srgb(src), size, a.anchor)
        dest = outdir / (stem + ".jpg")
        q = a.quality
        while True:
            im.save(dest, "JPEG", quality=q, optimize=True,
                    progressive=False, subsampling=0)   # 4:4:4, no chroma loss
            if dest.stat().st_size <= MAX_BYTES or q <= 80:
                break
            q -= 3
        kb = dest.stat().st_size // 1024
        note = f"  q{q}" if q != a.quality else ""
        print(f"  {kind:<7}{dest.name[:52]:<54}{kb} KB{note}")

    if skipped:
        print(f"\n  REFUSED {len(skipped)} file(s) below the target width — "
              f"regenerate at 2k rather than upscaling:")
        for nm, sz, need in skipped:
            print(f"    {nm[:50]:<52}{sz[0]}x{sz[1]}  needs {need}")
    print(f"\n  {len(files)-len(skipped)} file(s) -> {outdir}")
    print("  Upload these, not the PNGs.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
