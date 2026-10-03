"""
review_thumb.py — batch-2 review helper (Nova, W37). NOT shared pipeline code.

Makes small JPEGs of renders / plates / masters so a review reads a 90 KB
contact sheet instead of a 7 MB PNG, and can put a render side by side with
the plate it is supposed to match.

    python review_thumb.py --sheet out.jpg LABEL=path LABEL=path ...
    python review_thumb.py 900 path [path ...]      # individual thumbs
"""
import pathlib, sys
from PIL import Image, ImageDraw

ROOT = pathlib.Path(__file__).resolve().parents[2]      # personas/seoyeon
OUTD = ROOT / "_thumbs" / "w37b2"


def _resolve(p):
    q = pathlib.Path(p)
    return q if q.is_absolute() else (ROOT / q)


def thumbs(size, paths):
    OUTD.mkdir(parents=True, exist_ok=True)
    for p in paths:
        src = _resolve(p)
        im = Image.open(src).convert("RGB")
        im.thumbnail((size, size * 2))
        dst = OUTD / f"{src.stem}_{im.width}x{im.height}.jpg"
        im.save(dst, quality=82)
        print(dst, im.size)


def sheet(out, pairs, h=620, pad=10, label_h=34):
    OUTD.mkdir(parents=True, exist_ok=True)
    tiles = []
    for label, p in pairs:
        im = Image.open(_resolve(p)).convert("RGB")
        w = int(im.width * (h / im.height))
        tiles.append((label, im.resize((w, h), Image.LANCZOS)))
    W = sum(t[1].width for t in tiles) + pad * (len(tiles) + 1)
    canvas = Image.new("RGB", (W, h + label_h + pad), (16, 16, 16))
    d = ImageDraw.Draw(canvas)
    x = pad
    for label, im in tiles:
        canvas.paste(im, (x, label_h + pad))
        d.text((x + 2, 8), label, fill=(255, 230, 120))
        x += im.width + pad
    outp = OUTD / out
    canvas.save(outp, quality=80)
    print(outp, canvas.size)


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a:
        sys.exit(__doc__)
    if a[0] == "--sheet":
        out = a[1]
        pairs = [s.split("=", 1) for s in a[2:]]
        sheet(out, [(l.replace("__", " "), p) for l, p in pairs])
    else:
        thumbs(int(a[0]), a[1:])
