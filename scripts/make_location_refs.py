"""Create one small JPEG per location from the private originals (personas/seoyeon/locations/).

The committed copies let the runner keep places consistent without uploading the full-size set.
"""
import pathlib
from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parents[1] / "personas" / "seoyeon"
OUT = ROOT / "location_refs"


def main():
    OUT.mkdir(exist_ok=True)
    for folder in sorted(p for p in (ROOT / "locations").iterdir() if p.is_dir()):
        first = sorted(folder.glob(f"{folder.name}_0*.png"))
        if not first:
            continue
        with Image.open(first[0]) as im:
            im = im.convert("RGB")
            im.thumbnail((1024, 1024))
            target = OUT / f"{folder.name}.jpg"
            im.save(target, "JPEG", quality=82, optimize=True)
            print(f"{target.name}: {target.stat().st_size // 1024} KB")


if __name__ == "__main__":
    main()
