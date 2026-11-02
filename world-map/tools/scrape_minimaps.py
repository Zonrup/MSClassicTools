"""Slowly scrape the minimap image and portal info for every Victoria Island map from meowDB.

    python tools/scrape_minimaps.py            # crawl (resumable), then build data/minimap_info.js
    python tools/scrape_minimaps.py --build    # only rebuild data/minimap_info.js from saved files
    python tools/scrape_minimaps.py --limit 3  # stop after 3 new maps (for testing)

Every run ends by rewriting data/minimap_info.js from the saved files, so when that file
already exists the script refuses to run unless given --force_overwrite_existing_data
(it would drop hand-made entries, and every map without a raw file on this machine).

Every request to meowDB (page or image) is at least DELAY seconds after the last one.
Starts from the maps in data/raw/meowdb-pack.json and follows connected maps that stay on
Victoria Island, so new maps are picked up too.

Saves, per map:
  data/raw/minimaps/<mapId>.json  the map object meowDB embeds in its page (all fields)
  data/minimaps/<mapId>.png       the minimap image (when the map has one)
Maps already saved are skipped, so the script can be stopped and restarted at any time.
Delete a map's .json to fetch it again.

Minimap coordinates: a game point (x, y) sits at image pixel
  ((x + cx) * imgW / w, (y + cy) * imgH / h)
where w, h, cx, cy are minimapWidth/Height and miniMapCenterX/Y.
"""
import argparse
import json
import re
import struct
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = "https://meowdb.com/msclassic"
DELAY = 5.0  # seconds between any two requests to meowDB
UA = "Mozilla/5.0 (world-map minimap scrape; 1 request / 5s)"
RAW = ROOT / "data" / "raw" / "minimaps"
IMG = ROOT / "data" / "minimaps"
PACK = ROOT / "data" / "raw" / "meowdb-pack.json"
OUT_JS = ROOT / "data" / "minimap_info.js"

_last = 0.0


def get(url):
    """GET with a global rate limit and gentle retries. Returns (status, bytes)."""
    global _last
    for attempt in range(4):
        wait = _last + DELAY - time.monotonic()
        if wait > 0:
            time.sleep(wait)
        _last = time.monotonic()
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.status, r.read()
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return 404, b""
            err = f"HTTP {e.code}"
        except Exception as e:  # network hiccup
            err = str(e)
        backoff = 30 * (attempt + 1)
        log(f"  {err} for {url}; waiting {backoff}s")
        time.sleep(backoff)
    raise RuntimeError(f"gave up on {url}")


def log(msg):
    print(time.strftime("%H:%M:%S"), msg, flush=True)


def flight(html):
    """Join the Next.js flight chunks embedded in a page into one string."""
    parts = re.findall(r'self\.__next_f\.push\(\[1,"((?:[^"\\]|\\.)*)"\]\)', html)
    return "".join(json.loads('"' + p + '"') for p in parts)


def object_at(s, i):
    depth, in_str, j = 0, False, i
    while j < len(s):
        c = s[j]
        if in_str:
            if c == "\\":
                j += 2
                continue
            if c == '"':
                in_str = False
        elif c == '"':
            in_str = True
        elif c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                break
        j += 1
    return json.loads(s[i:j + 1])


def object_around(s, key):
    k = s.find(key)
    if k < 0:
        return None
    depth, i = 0, k
    while i >= 0:
        c = s[i]
        if c == "}":
            depth += 1
        elif c == "{":
            if depth == 0:
                break
            depth -= 1
        i -= 1
    return object_at(s, i)


def png_size(b):
    if b[:8] == b"\x89PNG\r\n\x1a\n":
        return struct.unpack(">II", b[16:24])
    return None


def crawl(limit):
    RAW.mkdir(parents=True, exist_ok=True)
    IMG.mkdir(parents=True, exist_ok=True)
    pack = json.loads(PACK.read_text(encoding="utf-8"))
    queue = list(pack["maps"].keys()) + [s[0] for s in pack["spots"]]
    seen, order = set(), []
    for q in queue:
        if q not in seen:
            seen.add(q)
            order.append(q)
    queue = order
    new = 0
    errors = {}
    while queue:
        mid = queue.pop(0)
        path = RAW / f"{mid}.json"
        if path.exists():
            m = json.loads(path.read_text(encoding="utf-8"))
        else:
            if limit is not None and new >= limit:
                break
            try:
                status, body = get(f"{BASE}/maps/{mid}")
                if status == 404:
                    errors[mid] = "404"
                    continue
                m = object_around(flight(body.decode("utf-8")), '"connectedMaps":[')
                if not m:
                    errors[mid] = "no map data in page"
                    continue
                if m.get("hasMinimapImage") and not (IMG / f"{mid}.png").exists():
                    s2, img = get(f"{BASE}/maps/minimaps/{mid}.png")
                    size = png_size(img) if s2 == 200 else None
                    if size:
                        (IMG / f"{mid}.png").write_bytes(img)
                        m["_imgSize"] = list(size)
                    else:
                        m["_imgError"] = f"status {s2}"
                path.write_text(json.dumps(m, ensure_ascii=False), encoding="utf-8")
                new += 1
                left = sum(1 for q in queue if not (RAW / f"{q}.json").exists())
                log(f"{mid} {m.get('name')!r} portals={len(m.get('portals') or [])} "
                    f"img={'yes' if (IMG / f'{mid}.png').exists() else 'no'} | new {new}, ~{left} left")
            except Exception as e:
                errors[mid] = str(e)
                log(f"{mid} FAILED: {e}")
                continue
        if m.get("region") == "VictoriaIsland":
            for c in m.get("connectedMaps") or []:
                n = c["mapId"]
                if n not in seen:
                    seen.add(n)
                    queue.append(n)
    log(f"crawl done: {new} new maps this run, errors: {errors or 'none'}")


def build():
    out = {}
    for p in sorted(RAW.glob("*.json")):
        m = json.loads(p.read_text(encoding="utf-8"))
        mid = m["id"]
        img = IMG / f"{mid}.png"
        out[mid] = {
            "name": m.get("name"),
            "street": m.get("streetName"),
            "region": m.get("region"),
            "town": bool(m.get("isTown")),
            "returnMap": m.get("returnMap"),
            "minimap": {
                "img": f"data/minimaps/{mid}.png" if img.exists() else None,
                "imgW": (m.get("_imgSize") or [None, None])[0],
                "imgH": (m.get("_imgSize") or [None, None])[1],
                "w": m.get("minimapWidth"), "h": m.get("minimapHeight"),
                "cx": m.get("miniMapCenterX"), "cy": m.get("miniMapCenterY"),
            },
            # Portals to other maps: [x, y, toMapId, toMapName, portalName, type]
            "portals": [[p["x"], p["y"], p.get("toMapId"), p.get("toMapName"), p.get("name"), p.get("type")]
                        for p in (m.get("portals") or [])],
            # Teleports inside the same map: [x, y, toX, toY]
            "intra": [[p["x"], p["y"], p.get("toX"), p.get("toY")] for p in (m.get("intraPortals") or [])],
            # NPCs: [x, y, name]
            "npcs": [[n["x"], n["y"], n.get("name")] for n in (m.get("npcs") or [])],
        }
    OUT_JS.write_text(
        "// Generated by tools/scrape_minimaps.py. Map id -> minimap image + portals/NPCs in game coords.\n"
        "window.MINIMAP_INFO = " + json.dumps(out, ensure_ascii=False, separators=(",", ":")) + ";\n",
        encoding="utf-8")
    log(f"wrote {OUT_JS.relative_to(ROOT)} with {len(out)} maps")


OVERWRITE_WARNING = """\
WARNING: this rewrites {out} from scratch, using only the saved files in {raw}/.

That would lose:
  - the hand-made entries for maps the crawl misses (Cabin of the Forsaken 010003112 and
    The Circulation Desk 010002005, see "Hand-added maps" in README.md), and
  - every map whose raw file isn't on this machine ({have} raw files here, {now} maps in
    the current file). data/raw/ isn't in the repo, so on a fresh checkout this wipes
    almost every minimap.

Nothing was changed. If you mean it, run again with --force_overwrite_existing_data,
then re-add the hand-made entries (or restore them with git)."""


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", action="store_true", help="only rebuild minimap_info.js")
    ap.add_argument("--limit", type=int, help="stop after this many new maps")
    ap.add_argument("--force_overwrite_existing_data", action="store_true",
                    help="allow replacing an existing minimap_info.js (see the warning without it)")
    a = ap.parse_args()
    # Every run ends by rewriting minimap_info.js, so refuse up front (before a long crawl)
    # unless the overwrite is asked for.
    if OUT_JS.exists() and not a.force_overwrite_existing_data:
        txt = OUT_JS.read_text(encoding="utf-8")
        now = len(json.loads(txt[txt.index("{", txt.index("window.MINIMAP_INFO")):txt.rindex("}") + 1]))
        have = len(list(RAW.glob("*.json"))) if RAW.exists() else 0
        print(OVERWRITE_WARNING.format(out=OUT_JS.relative_to(ROOT), raw=RAW.relative_to(ROOT), have=have, now=now),
              file=sys.stderr)
        sys.exit(2)
    if not a.build:
        try:
            crawl(a.limit)
        except KeyboardInterrupt:
            log("stopped; run again to resume")
            sys.exit(1)
    build()
