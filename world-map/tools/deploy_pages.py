"""Publish the world map into a GitHub Pages site repo.

    python world-map/tools/deploy_pages.py <site-repo> [--dest public/msclassicatlas] [--push]

Copies only the files the page needs (index.html, css/, js/, the data scripts and the
monster sprites; not tools/, data/raw/ or the README) into <site-repo>/<dest>, replacing
whatever was there, then commits that folder in the site repo. With --push it also pushes,
and the site's own Pages workflow publishes it.

The default dest suits an Astro site, which serves public/ as-is: public/msclassicatlas
becomes https://<site>/msclassicatlas/. The site repo path is an argument so no local
path is stored in either repo.
"""
import argparse
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent  # world-map/
# Everything index.html loads. Add new data files here, or the live page ships without them.
FILES = ["index.html", "css", "js", "data/terrain.js", "data/victoria.js", "data/mob_images.js", "data/mobs",
         "data/minimap_info.js", "data/minimaps", "data/drops.js", "data/items"]


def git(repo, *args, check=True):
    return subprocess.run(["git", "-C", str(repo), *args], check=check, capture_output=True, text=True).stdout.strip()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("site", type=Path, help="path to the GitHub Pages site repo")
    ap.add_argument("--dest", default="public/msclassicatlas", help="folder inside the site repo (default: %(default)s)")
    ap.add_argument("--push", action="store_true", help="push the site repo after committing")
    a = ap.parse_args()

    site = a.site.resolve()
    if git(site, "rev-parse", "--show-toplevel", check=False) == "":
        sys.exit(f"not a git repo: {a.site}")
    dest = (site / a.dest).resolve()
    if site not in dest.parents:
        sys.exit("--dest must be a folder inside the site repo")
    if git(site, "status", "--porcelain", "--", a.dest):
        sys.exit(f"{a.dest} has uncommitted changes in the site repo; commit or discard them first")

    if dest.exists():
        shutil.rmtree(dest)
    for rel in FILES:
        src, out = ROOT / rel, dest / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        if src.is_dir():
            shutil.copytree(src, out)
        else:
            shutil.copy2(src, out)

    git(site, "add", "-A", "--", a.dest)
    if not git(site, "status", "--porcelain", "--", a.dest):
        print("no changes to deploy")
        return
    src_rev = git(ROOT, "rev-parse", "--short", "HEAD", check=False) or "uncommitted"
    dirty = " (with uncommitted changes)" if git(ROOT, "status", "--porcelain", "--", ".", check=False) else ""
    git(site, "commit", "-m", f"Update MS Classic Atlas from MSClassicTools {src_rev}{dirty}", "--", a.dest)
    print(f"committed {a.dest} in the site repo")
    if a.push:
        print(subprocess.run(["git", "-C", str(site), "push"], capture_output=True, text=True).stderr.strip())


if __name__ == "__main__":
    main()
