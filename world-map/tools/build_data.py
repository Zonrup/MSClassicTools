"""Build data/victoria.js from the raw meowDB crawl.

Input (made by tools/crawl_meowdb.js, run in a browser tab on meowdb.com):
  data/raw/meowdb-pack.json  compact crawl: maps, monsters, and the game's world-map dots
    spots: [mapId, x, y, type (0 town, 2 area, 3 field), title, levelMin, levelMax, mapCount]
    maps:  mapId -> {n: name, s: street, t: isTown, l: linked mapIds, m: [[mobId, count, respawnSec]], p: [[toMapId, portalX]]}
    mobs:  mobId -> [name, isBoss, level, hp, exp, physDef, magicDef, accuracy, avoid]

Layout: maps that the game's world map shows as a dot are fixed at that dot
(times SCALE). Every other map is placed by a small force simulation:
links pull maps together, maps push each other apart, and each map is pulled
gently toward its nearest dot. Nodes you drag in Edit mode are saved with
"pinned": true, and this script keeps their positions on the next build.

Usage:  python tools/build_data.py
"""
import json
import math
import random
import re
import sys
from collections import deque
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "victoria.js"
SCALE = 6  # world units per world-map pixel; must match data/terrain.js

# Hand-placed positions (world units), by map name, for spots the force layout
# tangles. These win over Edit-mode pins.
MANUAL_POS = {
    # Empty: the hand-made layout is saved as pinned positions in data/victoria.js.
    # Entries here override those pins on the next build.
}


# Maps and monsters the meowDB crawl misses (reachable only from a map's edge or a building),
# added by hand from their meowdb.com pages, in the pack's own shapes. Links to them already
# come from the crawled maps that lead there.
EXTRA_MAPS = {
    # Through the portal at the west end of The Murky Swamp II; Shade, a timed boss.
    "010003112": {"name": "Cabin of the Forsaken", "street": "Hidden Street", "isTown": False,
                  "links": ["010003111"], "mobs": [{"id": "700006", "count": 1, "respawn": 3600}]},
    # Up at the top of the Magic Library; NPCs come from data/minimap_info.js.
    "010002005": {"name": "The Circulation Desk", "street": "Hidden Street", "isTown": True,
                  "links": ["010002003"], "mobs": []},
}
EXTRA_MOBS = {
    "700006": {"name": "Shade", "boss": True, "props": {
        "Level": 48, "HP": 47000, "EXP": 488, "Physical Defense": 30, "Magic Defense": 10,
        "Accuracy": 138, "Avoidability": 35}},
}
# Map types that node_type gets wrong. The Cabin is a hidden street whose only monster is a
# boss (node_type would call it "boss"; it gets the skull badge either way).
TYPE_OVERRIDES = {"010003112": "hidden"}


def load_js_object(path, var):
    txt = path.read_text(encoding="utf-8")
    start = txt.index("{", txt.index(var))
    return json.loads(txt[start:txt.rindex("}") + 1])


def slug(name):
    s = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
    return s or "map"


def main():
    pack = json.loads((RAW / "meowdb-pack.json").read_text(encoding="utf-8"))
    raw = {"crawledAt": pack.get("crawledAt")}
    maps = {
        i: {"id": i, "name": m["n"].strip(), "street": m["s"], "isTown": bool(m["t"]), "links": m["l"],
            "mobs": [{"id": str(x[0]), "count": x[1], "respawn": x[2]} for x in m["m"]]}
        for i, m in pack["maps"].items()
    }
    outside = {i: {"name": o["n"], "region": o["r"]} for i, o in pack.get("outside", {}).items()}
    keys = ["mapId", "x", "y", "type", "title", "levelMin", "levelMax", "mapCount"]
    world = {"spots": [dict(zip(keys, s)) for s in pack["spots"]]}
    mob_keys = ["Level", "HP", "EXP", "Physical Defense", "Magic Defense", "Accuracy", "Avoidability"]
    mobs_raw = {
        i: {"name": v[0], "boss": bool(v[1]), "props": {k: x for k, x in zip(mob_keys, v[2:]) if x is not None}}
        for i, v in pack["mobs"].items()
    }
    for i, m in EXTRA_MAPS.items():
        maps.setdefault(i, {"id": i, **m})
    for i, m in EXTRA_MOBS.items():
        mobs_raw.setdefault(i, m)

    # Previous positions: pinned maps always keep theirs; other maps keep theirs too unless
    # the build is run with --relayout.
    pinned, kept = {}, {}
    relayout = "--relayout" in sys.argv
    if OUT.exists():
        try:
            prev = load_js_object(OUT, "window.WORLD_DATA")
            for m in prev.get("maps", []):
                if not m.get("mapId") or m.get("section"):
                    continue
                if m.get("pinned"):
                    pinned[m["mapId"]] = (m["x"], m["y"])
                elif not relayout:
                    kept[m["mapId"]] = (m["x"], m["y"])
        except Exception as e:  # noqa: BLE001
            print("warning: could not read previous layout:", e)
    by_name = {m["name"]: i for i, m in maps.items()}
    for name, xy in MANUAL_POS.items():
        if name in by_name:
            pinned[by_name[name]] = xy
        else:
            print("warning: MANUAL_POS name not found:", name)

    # ---------------- monsters ----------------
    mobs = {}
    for mid, m in mobs_raw.items():
        p = m.get("props", {})
        entry = {
            "name": m.get("name") or f"Monster {mid}",
            "level": p.get("Level", 0),
            "hp": p.get("HP"),
            "exp": p.get("EXP"),
            "def": p.get("Physical Defense"),
            "mdef": p.get("Magic Defense"),
            "acc": p.get("Accuracy"),
            "avoid": p.get("Avoidability"),
            "meowdbId": int(mid),
        }
        if m.get("boss"):
            entry["boss"] = True
        mobs[f"m{mid}"] = {k: v for k, v in entry.items() if v is not None}

    # ---------------- graph ----------------
    ids = sorted(maps)
    adj = {i: set() for i in ids}
    exits = {i: [] for i in ids}
    for i in ids:
        for j in maps[i]["links"]:
            if j == i:
                continue
            if j in maps:
                adj[i].add(j)
                adj[j].add(i)
            else:
                o = outside.get(j, {})
                exits[i].append({"mapId": j, "name": o.get("name", j), "region": o.get("region", "?")})

    # ---------------- world-map dots ----------------
    spots = [s for s in world["spots"] if s["mapId"] in maps]
    spot_by_map = {s["mapId"]: s for s in spots}
    hubs = [s for s in spots if s["type"] in (0, 2)]  # towns and big dungeon areas

    def hub_name(s):
        return s["title"].strip()

    # Nearest dot (by link hops) for every map: multi-source BFS.
    anchor, hops = {}, {}
    q = deque()
    for s in spots:
        anchor[s["mapId"]] = s
        hops[s["mapId"]] = 0
        q.append(s["mapId"])
    while q:
        i = q.popleft()
        for j in adj[i]:
            if j not in anchor:
                anchor[j] = anchor[i]
                hops[j] = hops[i] + 1
                q.append(j)

    # Region = nearest town/dungeon dot (by distance on the world map) to the map's own dot.
    def region_of(s):
        if s["type"] in (0, 2):
            return slug(hub_name(s))
        best = min(hubs, key=lambda h: (h["x"] - s["x"]) ** 2 + (h["y"] - s["y"]) ** 2)
        return slug(hub_name(best))

    regions = {slug(hub_name(h)): {"name": hub_name(h)} for h in hubs}

    # ---------------- node types ----------------
    UNDERGROUND_STREETS = ("dungeon", "passage", "subway")
    # Optional areas the page can hide with a toggle, matched by map-ID prefix.
    AREAS = {"forgotten_hollow": "010006"}

    def is_underground(m):
        street = (m.get("street") or "").lower()
        return any(s in street for s in UNDERGROUND_STREETS)

    def is_town(m):
        """Real towns: world-map town/area dots, plus hubs like Sleepywood that open onto hunting maps."""
        if not m.get("isTown") or "hidden" in (m.get("street") or "").lower():
            return False
        s = spot_by_map.get(m["id"])
        if s and s["type"] in (0, 2):
            return True
        return len(adj[m["id"]]) >= 3 and any(maps[j]["mobs"] for j in adj[m["id"]])

    def node_type(m):
        if m["id"] in TYPE_OVERRIDES:
            return TYPE_OVERRIDES[m["id"]]
        street = (m.get("street") or "").lower()
        mob_list = m.get("mobs", [])
        all_boss = mob_list and all(mobs.get(f"m{x['id']}", {}).get("boss") for x in mob_list)
        if all_boss:
            return "boss"
        if is_town(m):
            return "town"
        if "hidden" in street:
            return "hidden"
        if m.get("isTown") or not mob_list:
            if not mob_list and len(adj[m["id"]]) <= 1:
                return "building"
            return "safe"
        if is_underground(m):
            return "dungeon"
        return "field"

    # ---------------- sections ----------------
    # A section is everything "behind" a root map, cut out of the island and laid out as a
    # tree in its own panel below it (panels stack in this order). The walk starts at the
    # root's links, minus `exclude` (links back to the surface), or only at `start` if given.
    # It never enters an earlier section, or an optional area (AREAS) other than its own `area`.
    # `stair: False` drops the long stairway from the root (for roots far from the panel) and
    # draws a small portal marker by the root instead, at `portal` (offset from the root).
    # `spine` forces the main line to run from the root to that map (default: longest branch).
    # `align: [member, other]` shifts the panel so `member` sits straight below `other`.
    # `leaves_above: True` puts dead-end maps that hang off the main line above it.
    SECTIONS = [
        {"id": "sleepywood_dungeon", "name": "Sleepywood Dungeon", "root": "010005000",
         "exclude": ["010005010"]},  # Swampy Land in a Deep Forest: the way back up
        {"id": "forgotten_hollow", "name": "Forgotten Hollow", "area": "forgotten_hollow",
         "root": "010002071",        # The Tree Tunnel At the Forest Up North
         "start": ["010006060"],     # Forgotten Entrance III
         "spine": "010006071",       # Forgotten Dungeon Tunnel, the far end (links to Sleepy Dungeon V)
         "align": ["010006071", "010005054"],
         "leaves_above": True,
         "stair": False, "portal": [0, -50], "label": "Tree Tunnel (Ellinia)"},
    ]
    SECTION_DX, SECTION_DY, SECTION_GAP = 125, 125, 330

    terrain = load_js_object(ROOT / "data" / "terrain.js", "window.WORLD_TERRAIN")
    isl = np.array(terrain["islands"][0]["points"], float)
    island_cx, island_bottom = (isl[:, 0].min() + isl[:, 0].max()) / 2, isl[:, 1].max()

    section_of, section_pos, sections_out = {}, {}, []
    next_top = island_bottom + SECTION_GAP
    for sec in SECTIONS:
        root = sec["root"]
        blocked = set(sec.get("exclude", [])) | {root} | set(section_of)
        own = AREAS.get(sec.get("area"))
        in_area = lambda j: any(j.startswith(p) for p in AREAS.values() if p != own)  # noqa: E731
        members = set(sec["start"]) if "start" in sec else {j for j in adj[root] if j not in blocked}
        q = deque(members)
        while q:
            i = q.popleft()
            for j in adj[i]:
                if j not in blocked and j not in members and not in_area(j):
                    members.add(j)
                    q.append(j)

        # Breadth-first tree from the root; the longest branch becomes the straight main line,
        # and every other branch drops onto a new row below.
        parent, depth, order = {root: None}, {root: 0}, [root]
        q = deque([root])
        while q:
            i = q.popleft()
            for j in sorted(adj[i]):
                if j in members and j not in depth:
                    parent[j], depth[j] = i, depth[i] + 1
                    order.append(j)
                    q.append(j)
        children = {i: [] for i in depth}
        for j, pj in parent.items():
            if pj is not None:
                children[pj].append(j)
        height = {}
        for i in reversed(order):
            height[i] = 1 + max((height[c] for c in children[i]), default=0)
        # Each branch takes the first row below its parent that is free for the branch's whole
        # length, so branches sit right under where they split off.
        row, taken = {}, {}
        spine = set()
        j = sec.get("spine")
        while j is not None and j in parent:
            spine.add(j)
            j = parent[j]

        def free(r, d0, d1):
            return not any(d in taken.get(r, ()) for d in range(d0, d1 + 1))

        def place(i, r):
            row[i] = r
            taken.setdefault(r, set()).add(depth[i])
            kids = sorted(children[i], key=lambda c: (c not in spine, -height[c], c))
            for k, c in enumerate(kids):
                if k == 0:
                    place(c, r)
                    continue
                if r == 0 and not children[c] and (sec.get("leaves_above") or node_type(maps[c]) == "building"):
                    # Shops off the main line go above it, keeping the rows below for branches.
                    r2 = -1
                    while not free(r2, depth[c], depth[c]):
                        r2 -= 1
                else:
                    r2 = r + 1
                    while not free(r2, depth[c] - 1, depth[c] + height[c] - 1):
                        r2 += 1
                place(c, r2)

        place(root, 0)
        top_row, bottom_row = min(row.values()), max(row.values())
        max_depth = max(depth.values())
        ox = island_cx - max_depth * SECTION_DX / 2
        if "align" in sec:
            member, other = sec["align"]
            ox = section_pos[other][0] - depth[member] * SECTION_DX
        oy = next_top - top_row * SECTION_DY
        for i in members:
            section_of[i] = sec["id"]
            section_pos[i] = (ox + depth[i] * SECTION_DX, oy + row[i] * SECTION_DY)
        next_top = oy + (bottom_row + 1) * SECTION_DY + SECTION_GAP

        tree = {frozenset((j, pj)) for j, pj in parent.items() if pj}
        cross = sorted({tuple(sorted((a, b))) for a in members | {root} for b in adj[a]
                        if (b in members or b == root) and frozenset((a, b)) not in tree})
        leaving = sorted({(a, b) for a in members for b in adj[a] if b not in members and b != root})
        print(f"section {sec['id']}: {len(members)} maps, {max_depth} deep, {bottom_row - top_row + 1} rows")
        if cross:
            print("  links that are not part of the tree:", [(maps[a]["name"], maps[b]["name"]) for a, b in cross])
        if leaving:
            print("  links out of the section:", [(maps[a]["name"], maps[b]["name"]) for a, b in leaving])
        out = {"id": sec["id"], "name": sec["name"], "root": root,
               "entry": {"x": int(round(ox)), "y": int(round(oy))}}
        if "label" in sec:
            out["label"] = sec["label"]
        if sec.get("stair") is False:
            out["stair"] = False
            out["portal"] = {"dx": sec.get("portal", [0, -50])[0], "dy": sec.get("portal", [0, -50])[1]}
        sections_out.append(out)

    # ---------------- layout ----------------
    rng = random.Random(7)
    n = len(ids)
    index = {i: k for k, i in enumerate(ids)}
    pos = np.zeros((n, 2))
    fixed = np.zeros(n, bool)
    home = np.zeros((n, 2))
    types = {i: node_type(maps[i]) for i in ids}

    for i in ids:
        k = index[i]
        a = anchor.get(i)
        ax, ay = (a["x"] * SCALE, a["y"] * SCALE) if a else (1900, 1500)
        home[k] = (ax, ay)
        if i in section_pos:
            pos[k] = section_pos[i]
            fixed[k] = True
        elif i in pinned:
            pos[k] = pinned[i]
            fixed[k] = True
        elif i in kept:
            pos[k] = kept[i]
            fixed[k] = True
        elif i in spot_by_map:
            pos[k] = (ax, ay)
            fixed[k] = True
        else:
            r = 40 + 30 * hops.get(i, 3)
            ang = rng.random() * math.tau
            pos[k] = (ax + math.cos(ang) * r, ay + math.sin(ang) * r)

    # Links into a section don't pull on the island layout.
    edges = np.array([(index[i], index[j]) for i in ids for j in adj[i]
                      if i < j and i not in section_of and j not in section_of], int)
    small = np.array([types[i] == "building" for i in ids])
    rest = np.where(small[edges[:, 0]] | small[edges[:, 1]], 40.0, 105.0) if len(edges) else np.array([])

    for step in range(900):
        t = 1 - step / 900
        force = np.zeros_like(pos)
        # repulsion (all pairs)
        d = pos[:, None, :] - pos[None, :, :]
        dist2 = (d ** 2).sum(-1) + 1e-3
        np.fill_diagonal(dist2, np.inf)
        min_d = np.where(small[:, None] | small[None, :], 34.0, 80.0)
        rep = np.where(dist2 < (min_d * 2.2) ** 2, (min_d ** 2) / dist2, 0.0)
        force += (d * (rep / np.sqrt(dist2))[:, :, None]).sum(1) * 1.2
        # springs
        if len(edges):
            v = pos[edges[:, 1]] - pos[edges[:, 0]]
            L = np.sqrt((v ** 2).sum(1)) + 1e-6
            f = ((L - rest) / L)[:, None] * v * 0.08
            np.add.at(force, edges[:, 0], f)
            np.add.at(force, edges[:, 1], -f)
        # pull toward own world-map dot
        force += (home - pos) * 0.012
        force[fixed] = 0
        step_len = np.sqrt((force ** 2).sum(1, keepdims=True)) + 1e-9
        pos += force / step_len * np.minimum(step_len, 25 * t + 1)

    # ---------------- output ----------------
    out_maps = []
    used = set()
    id_of = {}
    for i in ids:
        base = slug(maps[i]["name"])
        sid = base if base not in used else f"{base}_{i}"
        used.add(sid)
        id_of[i] = sid

    for i in ids:
        m = maps[i]
        k = index[i]
        a = anchor.get(i)
        entry = {
            "id": id_of[i],
            "name": m["name"],
            "mapId": i,
            "region": region_of(a) if a else "unknown",
            "type": types[i],
            "street": m.get("street"),
            "x": int(round(pos[k][0])),
            "y": int(round(pos[k][1])),
            "mobs": [{"id": f"m{x['id']}", "count": x["count"]} for x in m.get("mobs", [])],
            "links": sorted(id_of[j] for j in adj[i] if j > i),
            "verified": True,
        }
        if is_underground(m):
            entry["layer"] = "underground"
        for area, prefix in AREAS.items():
            if i.startswith(prefix):
                entry["area"] = area
        if i in section_of:
            entry["section"] = section_of[i]
        if i in pinned and i not in section_of:
            entry["pinned"] = True
        if exits[i]:
            entry["exits"] = exits[i]
        if i in spot_by_map:
            entry["worldMapDot"] = True
        out_maps.append(entry)

    data = {
        "meta": {
            "name": "Victoria Island",
            "status": "meowdb",
            "source": "https://meowdb.com/msclassic",
            "crawledAt": raw.get("crawledAt"),
            "scale": SCALE,
        },
        "regions": regions,
        "mobs": dict(sorted(mobs.items(), key=lambda kv: (kv[1]["level"], kv[1]["name"]))),
        "maps": out_maps,
        "sections": [{**s, "root": id_of[s["root"]]} for s in sections_out],
        "routes": [],
    }

    body = json.dumps(data, indent=1, ensure_ascii=False)
    OUT.write_text(
        "// GENERATED by tools/build_data.py from the meowDB crawl in data/raw/. Do not edit by hand:\n"
        "// drag nodes in Edit mode, download this file, then re-run the build to keep pinned positions.\n"
        "window.WORLD_DATA = " + body + ";\n",
        encoding="utf-8",
    )
    counts = {}
    for m in out_maps:
        counts[m["type"]] = counts.get(m["type"], 0) + 1
    print(f"wrote {OUT.relative_to(ROOT)}: {len(out_maps)} maps, {len(mobs)} monsters, types {counts}")
    unanchored = [maps[i]["name"] for i in ids if i not in anchor]
    if unanchored:
        print("not connected to any world-map dot:", unanchored)


if __name__ == "__main__":
    main()
