"""Write node positions dumped from the running page into data/victoria.js, as-is.

Use this to keep a layout made in Edit mode without the Download button. In the page's
DevTools console (or an agent's JS tool on the browser pane), run:

    copy(JSON.stringify(Object.fromEntries(window.worldMap.DATA.maps.map(m => [m.id, [m.x, m.y, m.pinned ? 1 : 0]]))))

save the clipboard to a file, then:

    python tools/save_positions.py positions.json

It only changes x, y and "pinned"; nothing else in victoria.js is touched, and the build is
not re-run. Maps in a section get their position from the section layout on the next build,
so moving them here doesn't last.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

pos = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
path = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / "data" / "victoria.js"
txt = path.read_text(encoding="utf-8")
s = txt.index("{", txt.index("window.WORLD_DATA"))
e = txt.rindex("}") + 1
data = json.loads(txt[s:e])
moved = 0
ids = set()
for m in data["maps"]:
    ids.add(m["id"])
    if m["id"] not in pos:
        continue
    x, y, pin = pos[m["id"]]
    if (m["x"], m["y"]) != (x, y):
        moved += 1
    m["x"], m["y"] = x, y
    if pin:
        m["pinned"] = True
    else:
        m.pop("pinned", None)
path.write_text(txt[:s] + json.dumps(data, indent=1, ensure_ascii=False) + txt[e:], encoding="utf-8")
print(f"maps {len(ids)} | moved {moved} | not in dump {sorted(i for i in ids if i not in pos)}")
