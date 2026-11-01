"""Slowly scrape monster drops from meowDB and build data/drops.js.

    python3 tools/scrape_drops.py            # crawl (resumable), then build data/drops.js
    python3 tools/scrape_drops.py --build    # only rebuild data/drops.js from saved files

One request every DELAY (10) seconds, one at a time, and it stops for good on a 403 or 429.
Every monster in data/victoria.js is fetched in three passes, so the drop lists arrive first:
  1. data/raw/drops/<meowdbId>.json      /msclassic/api/drops?monsterId=<id> (community drops + votes)
  2. data/items/<iconKey>.png            icons of the items that make it into drops.js
  3. data/raw/drops/<meowdbId>.osm.json  OSMLib reference rates, parsed from the monster's page
Files already saved are skipped, so it can be stopped and restarted at any time.

Which drops are kept (see KEEP_TYPES / MIN_SCORE): ETC items with a net vote score of 3 or more.
"""
import json
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = "https://meowdb.com/msclassic"
DELAY = 10.0  # seconds between any two requests to meowDB
UA = "MSClassicAtlas-drops/1.0 (+https://liujason.me/msclassicatlas; 1 request / 10s)"
RAW = ROOT / "data" / "raw" / "drops"
ICONS = ROOT / "data" / "items"
OUT_JS = ROOT / "data" / "drops.js"
KEEP_TYPES = {"Etc"}
MIN_SCORE = 3

_last = 0.0


class Blocked(Exception):
    pass


def log(msg):
    print(time.strftime("%H:%M:%S"), msg, flush=True)


def get(url):
    """GET with the global rate limit. Returns bytes, or None on 404. Raises Blocked on 403/429."""
    global _last
    for attempt in range(3):
        wait = _last + DELAY - time.monotonic()
        if wait > 0:
            time.sleep(wait)
        _last = time.monotonic()
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            if e.code in (403, 429):
                raise Blocked(f"HTTP {e.code} for {url}")
            err = f"HTTP {e.code}"
        except Exception as e:  # network hiccup
            err = str(e)
        log(f"  {err} for {url}; waiting {60 * (attempt + 1)}s")
        time.sleep(60 * (attempt + 1))
    raise RuntimeError(f"gave up on {url}")


def load_js_object(path):
    txt = path.read_text(encoding="utf-8")
    return json.loads(txt[txt.index("{"):txt.rindex("}") + 1])


def flight(html):
    """Join the Next.js flight chunks embedded in a page into one string."""
    parts = re.findall(r'self\.__next_f\.push\(\[1,"((?:[^"\\]|\\.)*)"\]\)', html)
    return "".join(json.loads('"' + p + '"') for p in parts)


def osmlib_rates(html):
    """{item name: percent} from the page's "OSMLib Reference Drop Rates" table."""
    s = flight(html)
    i = s.find("osmlib-drop-rates")
    if i < 0:
        return {}
    end = s.find('"section"', i + 20)
    rates = {}
    for row in s[i:end if end > 0 else i + 40000].split('["$","tr"')[1:]:
        n = re.search(r'break-words","children":"([^"]+)"', row)
        p = re.search(r'"children":"([\d.]+)%"', row)
        if n and p:
            rates[n.group(1)] = float(p.group(1))
    return rates


def kept(drops):
    return [d for d in drops if d.get("itemType") in KEEP_TYPES and d.get("score", 0) >= MIN_SCORE]


def mob_ids():
    data = load_js_object(ROOT / "data" / "victoria.js")
    return {k: v["meowdbId"] for k, v in data["mobs"].items() if v.get("meowdbId")}


def crawl():
    RAW.mkdir(parents=True, exist_ok=True)
    ICONS.mkdir(parents=True, exist_ok=True)
    ids = sorted(set(mob_ids().values()))
    log(f"{len(ids)} monsters")
    for n, mid in enumerate(ids, 1):  # 1. drop lists
        f = RAW / f"{mid}.json"
        if f.exists():
            continue
        body = get(f"{BASE}/api/drops?monsterId={mid}")
        drops = json.loads(body)["drops"] if body else []
        f.write_text(json.dumps(drops, ensure_ascii=False), encoding="utf-8")
        log(f"[{n}/{len(ids)}] drops {mid}: {len(drops)} ({len(kept(drops))} kept)")
    build()  # the map can use the drops before the slower passes finish

    icons = sorted({d["itemIconKey"] for mid in ids for d in kept(load_drops(mid)) if d.get("itemIconKey")})
    for n, key in enumerate(icons, 1):  # 2. icons
        f = ICONS / f"{key}.png"
        if f.exists():
            continue
        body = get(f"{BASE}/api/assets/icons/{key}")
        if body:
            f.write_bytes(body)
        log(f"[{n}/{len(icons)}] icon {key}")
    build()

    for n, mid in enumerate(ids, 1):  # 3. OSMLib rates
        f = RAW / f"{mid}.osm.json"
        if f.exists() or not kept(load_drops(mid)):
            continue
        body = get(f"{BASE}/monsters/{mid}")
        rates = osmlib_rates(body.decode("utf-8", "replace")) if body else {}
        f.write_text(json.dumps(rates, ensure_ascii=False), encoding="utf-8")
        log(f"[{n}/{len(ids)}] osmlib {mid}: {len(rates)} rates")
    build()


def load_drops(mid):
    f = RAW / f"{mid}.json"
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else []


def build():
    items, mobs = {}, {}
    for key, mid in mob_ids().items():
        osm_f = RAW / f"{mid}.osm.json"
        osm = json.loads(osm_f.read_text(encoding="utf-8")) if osm_f.exists() else {}
        rows = []
        for d in sorted(kept(load_drops(mid)), key=lambda d: -d["score"]):
            iid = str(d["itemId"])
            icon = d.get("itemIconKey")
            items[iid] = {"name": d["itemName"].strip(), "sub": d.get("itemSubtype") or "",
                          "icon": f"data/items/{icon}.png" if icon and (ICONS / f"{icon}.png").exists() else None}
            rows.append([iid, d["score"], osm.get(d["itemName"])])
        if rows:
            mobs[key] = rows
    out = {"meta": {"source": "meowdb.com community drops", "keep": sorted(KEEP_TYPES), "minScore": MIN_SCORE,
                    "builtAt": time.strftime("%Y-%m-%d")},
           "items": dict(sorted(items.items(), key=lambda kv: kv[1]["name"])), "mobs": mobs}
    OUT_JS.write_text(
        "// Generated by tools/scrape_drops.py. mobs: monster key -> [[itemId, vote score, OSMLib % or null]].\n"
        "window.WORLD_DROPS = " + json.dumps(out, ensure_ascii=False, indent=1) + ";\n", encoding="utf-8")
    log(f"wrote {OUT_JS.name}: {len(items)} items, {len(mobs)} monsters with drops")


if __name__ == "__main__":
    if "--build" in sys.argv:
        build()
    else:
        try:
            crawl()
        except Blocked as e:
            log(f"STOPPED: {e}. meowDB asked us to stop; not retrying.")
            build()
            sys.exit(1)
