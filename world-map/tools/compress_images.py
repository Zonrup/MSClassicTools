"""Shrink the page's PNG images (minimaps and monster sprites) to save bandwidth.

    python3 tools/compress_images.py            # compress, keeping originals
    python3 tools/compress_images.py --dry-run  # only report what it would save

Needs Pillow (pip install Pillow). For each PNG in data/minimaps/ and data/mobs/:
  - the original is kept next to it as <name>_original.png (the page never loads those,
    and tools/deploy_pages.py leaves them out);
  - the file itself is rewritten as a 256-colour palette PNG, and monster sprites
    taller than 144 px (DIRS) are scaled down to it (the page shows them at most 72 px tall).
A file is only replaced when that saves at least MIN_SAVING; otherwise it's left alone,
with no _original copy. Files that already have an _original are skipped, so the script
is safe to run again after new images are scraped.

Animated GIF sprites become lossless animated WebP (about half the size, same pixels and
timing): mob_<id>.gif is kept as mob_<id>_original.gif, mob_<id>.webp is written, and the
references in data/mob_images.js and index.html are switched to the .webp.
"""
import argparse
import io
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    sys.exit("needs Pillow: pip install Pillow")

ROOT = Path(__file__).resolve().parent.parent
DIRS = {"data/minimaps": None, "data/mobs": 144}  # folder -> max height (None: keep size)
MIN_SAVING = 0.10
REFS = ["data/mob_images.js", "index.html"]  # files that name sprite files


def compressed(path, max_h):
    im = Image.open(path).convert("RGBA")
    if max_h and im.height > max_h:
        im = im.resize((round(im.width * max_h / im.height), max_h), Image.LANCZOS)
    q = im.quantize(colors=256, method=Image.Quantize.FASTOCTREE, dither=Image.Dither.FLOYDSTEINBERG)
    buf = io.BytesIO()
    q.save(buf, "PNG", optimize=True)
    return buf.getvalue()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true", help="report savings without changing files")
    a = ap.parse_args()
    for rel, max_h in DIRS.items():
        before = after = done = kept = skipped = 0
        for p in sorted((ROOT / rel).glob("*.png")):
            if p.stem.endswith("_original"):
                continue
            orig = p.with_name(f"{p.stem}_original.png")
            if orig.exists():
                skipped += 1
                continue
            old = p.stat().st_size
            new = compressed(p, max_h)
            if len(new) > old * (1 - MIN_SAVING):
                kept += 1
                before += old; after += old
                continue
            before += old; after += len(new); done += 1
            if not a.dry_run:
                p.rename(orig)
                p.write_bytes(new)
        print(f"{rel} PNGs: {done} compressed, {kept} left as they were (under {MIN_SAVING:.0%} saving), "
              f"{skipped} already done; {before / 1e3:.0f} kB -> {after / 1e3:.0f} kB"
              + (" (dry run)" if a.dry_run else ""))
    gifs_to_webp(a.dry_run)


def gif_to_webp_bytes(path):
    """Lossless animated WebP with each frame's own duration (Pillow otherwise uses only
    the first frame's, or none) and the GIF's loop count."""
    im = Image.open(path)
    n = getattr(im, "n_frames", 1)
    durations = []
    for i in range(n):
        im.seek(i)
        durations.append(im.info.get("duration", 100) or 100)
    im.seek(0)
    buf = io.BytesIO()
    im.save(buf, "WEBP", save_all=True, lossless=True, method=6,
            duration=durations if n > 1 else durations[0], loop=im.info.get("loop", 0))
    return buf.getvalue()


def gifs_to_webp(dry_run):
    before = after = done = 0
    renamed = {}
    for p in sorted((ROOT / "data" / "mobs").glob("*.gif")):
        if p.stem.endswith("_original"):
            continue
        webp = p.with_suffix(".webp")
        data = gif_to_webp_bytes(p)
        old, new = p.stat().st_size, len(data)
        if new > old * (1 - MIN_SAVING):
            continue
        before += old; after += new; done += 1
        renamed[p.name] = webp.name
        if not dry_run:
            p.rename(p.with_name(f"{p.stem}_original.gif"))
            webp.write_bytes(data)
    if renamed and not dry_run:
        for rel in REFS:
            f = ROOT / rel
            text = f.read_text(encoding="utf-8")
            for old, new in renamed.items():
                text = text.replace(f"data/mobs/{old}", f"data/mobs/{new}")
            f.write_text(text, encoding="utf-8")
    print(f"data/mobs GIFs: {done} converted to WebP; {before / 1e3:.0f} kB -> {after / 1e3:.0f} kB"
          + (" (dry run)" if dry_run else ""))


if __name__ == "__main__":
    main()
