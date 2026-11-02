# Victoria Island — Expanded World Map

An interactive, full-screen map of every Victoria Island map in MapleStory Classic, drawn on an HTML canvas in the style of the in-game world map. It covers fields, hidden streets, dungeons and shops. Click a node to see its monsters and links in a side panel. Each node is colored by how hard it is for your level, like World of Warcraft's quest colors.

## Run it

```bash
python3 world-map/tools/serve.py
```

Run it from the repo root (the folder that holds `world-map/`), then open http://localhost:8765. `serve.py` is Python's file server plus `Cache-Control: no-cache`, so a normal reload always picks up edited files (plain `python3 -m http.server` lets the browser keep stale copies). `.claude/launch.json` in the repo root has this as the `world-map` config, so an agent can start it with `preview_start` `name: "world-map"`. Opening `index.html` straight from disk also mostly works, since the data files are scripts and not JSON.

**For agents:**
- The server may already be running (another session may have started it on port 8765). Check http://localhost:8765 first; if it answers, use it, or call `preview_start` with `name: "world-map"`, which reuses a running server. Starting a second copy on the same port fails.
- There's no live reload: the page never refreshes itself when a file changes. After each edit, reload your own test tab (a normal reload is enough with `serve.py`). Don't reload the user's tab: unsaved Edit-mode moves live only there.

## Deploying (liujason.me/msclassicatlas)

The live copy is served from the GitHub Pages site repo `Zonrup/zonrup.github.io` (an Astro site; anything in its `public/` folder is published unchanged). From this repo's root:

```bash
python3 world-map/tools/deploy_pages.py <path to your zonrup.github.io checkout> --push
```

It copies only what the page needs (`index.html`, `css/`, `js/`, the `data/*.js` scripts, and the images in `data/mobs/`, `data/minimaps/` and `data/items/`; the list is `FILES` in the script, so add new data files there) into the site repo's `public/msclassicatlas/`, replacing what was there, commits that folder and pushes. The site's own workflow then builds and publishes it in a minute or two. Leave off `--push` to look at the commit first; `--dest` changes the folder. Commit here first so the deploy commit names the right source revision.

## Controls

- Drag to pan, scroll wheel or pinch to zoom, `Home` or ⤢ to fit everything, `+` / `-` to zoom. Typing letters, digits or space anywhere starts a search.
- **Search** ("Search and monster picker" section of `js/map.js`):
  - **Typing:** type in the search box, or just start typing anywhere on the map. From 2 characters (`SEARCH_MIN_CHARS`), monsters, ETC items, NPCs and maps whose names start with the text match (maps also ignoring a leading "The"). If 3 or fewer monster names match (`SEARCH_MAX_MOBS`), every map holding them gets a teal ring as you type. The same goes for items, which ring the maps of every monster that drops them ("tree branch" rings the Stump maps), and NPCs.
  - **Crafting stations** are NPCs on the minimaps. They also match their craft's name and "crafting station" (`STATIONS` in `js/map.js`), so "smithing" finds the Anvil and "tailoring" the Sewing Machine; matches that are all stations ring together however many there are. Enter just leaves the box (the rings stay). Esc on the map clears it.
  - **Picker** ("Find anything"): the mushroom icon at the right of the search box opens a dialog with three tabs, **Monsters**, **NPCs** and **Items** (`PICK_TABS`, `renderPicker`), each with its match count. Picks on every tab ring together: NPCs ring their maps, items ring the maps of every monster that drops them. The filter matches all tabs; a tab with no match is greyed out but still opens (showing "No matching …"), and each edit of the filter switches to the first tab with a match when the open one has none (`onFilterChange`). Monster cards are sorted by level: sprite, name coloured by difficulty at your level, level(s), map count (same-name variants merged). It's next in tab order after the box, so type → Tab → Enter opens it with the typed text as the filter (focus returns to the icon on close). Click cards to pick any number; their maps get rings, live. The picks show as "Selected" chips at the top of the dialog (`renderPickedChips`); × on a chip removes that pick. Its filter narrows the cards (substring of the monster's name or of one of its drops) and shows map-name chips that jump to the map.
  - **Drops:** hovering a card, or a monster row in the side panel, shows that monster's common drops (`showDrops`), with OSMLib's reference rate where known.
  - Rings come from what's typed and the picks together (plus the dialog filter's matches while nothing is picked). The box under the search bar has a row for each: **Typed** (what the typing matches) and **Picked**. Each row's × clears just that row; Esc on the map clears the typing first, then the picks.
  - **Side panel:** monster rows that are typed or picked, or that drop a typed item, are marked in the light teal of the world map's rings, with a "Drops <item>" line (`paintMobs`). Found NPC rows, minimap dots and building pins use the same teal (`paintNpcs`). Every search hit, monster, item or NPC, gets one teal ring on the world map.
  - **Map tooltip:** while anything is typed or picked, hovering a map adds a light blue section listing which of those monsters, items and NPCs are on it (or in its buildings). Each item sits under the monster there that drops it, e.g. "Stump" with "• Tree Branch" (`selectedHereHtml`, from `state.sel`).
- Click a node to open its details on the right. `Esc` closes the panel. The URL keeps the selected map (`#map=<id>`), so links can be shared.
- Set your level (top left) to recolor every node and monster.
- Toggles: **Hidden streets**, **Forgotten Hollow**, plus the **Labels** slider (None / Smart / All). They're saved in `localStorage` under `wm-prefs`.
- Labels (`drawLabels` in `js/map.js`):
  - **None:** only the hovered/selected map and search hits. **All:** every map, overlaps allowed.
  - **Smart:** shows labels in zoom steps by camera scale (`SMART_ZOOM`; scale decides the room between nodes on any window size, and fitting the whole map is about 0.18 on a laptop and 0.3–0.4 on a 2560-wide screen): below 0.2 town banners only; from 0.2 area names along numbered side paths; from 0.6 names of maps on main roads; from 0.9 every map. Each smart label keeps `LABEL_PAD` (8 px) clear around it. Labels never overlap another label, a node, a section banner/marker or a HUD card, and each tries below, above, right, then left of its node (`labelPriority` sets the order).
  - Font: Atkinson Hyperlegible bold (`LABEL_FAMILY`), 14 px map names, 12 px level lines, 16 px italic area names (`LABEL_SIZE`, `LV_SIZE`, `SERIES_SIZE`).
  - Main roads (`routeScore`): for every pair of island towns, the shortest walk (fewest maps, then distance). A map's score is how many of those walks use it; 0 means a side path.
  - Series (`series`): linked runs of maps named `<base> I, II, ...` or `<base> 1, 2, ...`. Smart shows the base name once, in italics, tilted along the run. From 2× members on a main road get their own labels; from 3× the run splits into map names where they fit (`SERIES_FIT`).
  - Hand-picked areas (`AREA_GROUPS` in `js/map.js`): for areas whose maps don't share a numbered name, or a single big map that deserves an area name (shown just under its node). List an area name and its map ids; those maps leave any automatic series. Currently: Golem Temple (The Entrance of Golem's Temple, The Breathing Rock, Golem's Temple I–IV) and 3-Way Road-Split.
  - Area names try several spots (`placeSeries`): the middle of the run along its main direction, the middle of each link inside the run along that link, then on each map, each also flat; the first spot clear of other labels and other maps' nodes wins.
  - Knobs: `SMART_ZOOM`, `LABEL_PAD`, `SERIES_FIT`, the priorities in `labelPriority`. `window.worldMap.routeScore` and `.series` are exposed for debugging.
- Backtick (`` ` ``) or **Edit layout**: drag nodes (see [Changing the layout](#changing-the-layout)).

## Level colors

Each monster's color comes from its level minus your level (`diffFor` in `js/map.js`). The cut-offs change with your level (`diffBands`):

| Color | Level under 10 | 10–19 | 20 and up |
|---|---|---|---|
| Red (too hard) | 4+ above | 3+ above | 2+ above |
| Orange (hard) | 0–3 above | 0–2 above | 1 below to 1 above |
| Yellow (good farming) | 1–5 below | 1–(5 + level/10) below | 2–(5 + level/10) below |
| Green (easy) | down to 10 below | down to 10 below | down to 10 + (level − 19)/2 below, max 15 |
| Grey (trivial) | further below | further below | further below |

Anchors from play: at level 29, green/blue mushrooms (14–19) are easy, Ant Tunnel (22–27) is good farming, 28–30 hard, 31+ too hard. Before leaving Maple Island, snails and shrooms are farming while slimes, pigs and orange mushrooms are hard.

A map's node takes the level that a third of its spawns are at or above (`HARD_SHARE` in `levelRange`), not the average. Otherwise a crowd of snails would hide the stumps and orange mushrooms you keep running into. Bosses don't count unless the map has nothing else. This stands in for the real question, which is how many hits a monster takes. meowDB gives HP, defense and avoid for every monster, and they're already in the data, so it could later become a damage-based check.

## Files

| File | What it is | Edit by hand? |
|---|---|---|
| `index.html` | Page shell: canvas, HUD, legend, side panel, picker dialog, edit bar. Loads the `data/*.js` scripts, then `js/map.js`. | Yes |
| `css/style.css` | Parchment-style UI. Colors are tokens on `:root`. | Yes |
| `js/map.js` | Everything else: rendering, input, panel. One IIFE, no build step, no libraries. | Yes |
| `data/terrain.js` | `window.WORLD_TERRAIN`: island outlines and biome patches, all hand-drawn. `rivers` is empty (the old Kerning–Sleepywood river was removed) but still supported. | Yes |
| `data/victoria.js` | `window.WORLD_DATA`: maps, links, monsters, sections. Generated by `tools/build_data.py`. | Positions only (see below) |
| `data/raw/meowdb-pack.json` | Raw meowDB crawl, the input to the build. | No, re-crawl instead |
| `tools/crawl_meowdb.js` | Browser-console script that crawls meowDB and downloads the pack. | Yes |
| `tools/fetch_mob_images.py` | Downloads every monster's sprite from meowDB into `data/mobs/` and writes `data/mob_images.js`. | Yes |
| `tools/deploy_pages.py` | Copies the page into the GitHub Pages site repo and commits/pushes it (see Deploying). | Yes |
| `data/mobs/`, `data/mob_images.js` | Monster sprites (PNG or animated GIF) and the monster key → file index. | No, re-run the fetch |
| `tools/scrape_drops.py` | Fetches every monster's drops from meowDB and writes `data/drops.js` (see Monster drops). | Yes |
| `data/drops.js`, `data/items/` | `window.WORLD_DROPS`: common ETC drops per monster, and the item icons. | No, re-run the scrape |
| `tools/build_data.py` | Turns the pack into `victoria.js`. Needs `numpy`. | Yes |
| `tools/save_positions.py` | Writes positions dumped from the running page into `victoria.js`. | Yes |
| `tools/scrape_minimaps.py` | Fetches each map's minimap image, portals and NPCs from meowDB and writes `data/minimap_info.js`. Refuses to replace an existing `minimap_info.js` without `--force_overwrite_existing_data`. | Yes |
| `data/minimap_info.js`, `data/minimaps/` | `window.MINIMAP_INFO`: minimap image, portal pins and NPCs per map id, and the images. Loads deferred. | No, re-run the scrape |
| `tools/serve.py` | Local dev server with `Cache-Control: no-cache` (see Run it). | Yes |

Fonts are Fredoka (UI), Atkinson Hyperlegible (map labels) and Alegreya SC (titles), from Google Fonts.

## Data

All map and monster data comes from [meowDB](https://meowdb.com/msclassic): 248 Victoria Island maps and 76 monsters, crawled 2026-10-31 (two maps and one monster added by hand, see below); monster drops crawled 2026-11-01.

### Hand-added maps

The crawl missed two maps, which only showed up as unnamed "Leads off this map" exits. They were added by hand from their meowDB pages:

- **Cabin of the Forsaken** (`010003112`), off the west end of The Murky Swamp II, with the boss Shade (Lv 48). It's a hidden street with a skull badge; `TYPE_OVERRIDES` keeps it from being typed `boss`.
- **The Circulation Desk** (`010002005`), at the top of the Magic Library, with Lyn the Librarian, Sabrina the Scribe and Jon the Justicar. It's a building inside the Magic Library, which is now drawn as a safe zone instead of being hidden as one of Ellinia's buildings.

Where they live, so a rebuild keeps them:

- `EXTRA_MAPS`, `EXTRA_MOBS` and `TYPE_OVERRIDES` at the top of `tools/build_data.py` add them to the crawl before the build runs.
- `data/victoria.js` is written by that build, so it has them too.
- `data/minimap_info.js` has hand-made entries for both (no minimap image on meowDB; NPC and portal positions unknown, so `null`). `tools/scrape_minimaps.py` rebuilds that file from `data/raw/minimaps/` at the end of every run, so it refuses to run while the file exists unless you pass `--force_overwrite_existing_data`; after a forced run, re-add these two entries (or restore them with git).
- `data/raw/` (the crawl pack, raw minimap and drop files) is not in the repo; it only exists on the machine that crawled. On a fresh checkout, neither build can run, and a forced minimap rebuild would wipe almost every minimap.

### Monster drops

`tools/scrape_drops.py` reads meowDB's community drop lists (`/msclassic/api/drops?monsterId=<id>`): items players have confirmed in MS Classic, with up and down votes. It keeps ETC items with a net score of 3 or more (`KEEP_TYPES`, `MIN_SCORE`). Equips and USE items are left out for now. It also saves the item icons, and the OSMLib reference rates from each monster's page.

- meowDB's robots.txt asks tools to email contact@meowdb.com for permission first, and approved tools to send one request every 10 seconds with the tool's name and a contact in the User-Agent, and to stop on a 403 or 429. The script keeps to the pace, user agent and stop rules.
- It takes about 40 minutes and can be stopped and restarted; saved files are skipped. Raw responses go to `data/raw/drops/`. `python3 tools/scrape_drops.py --build` rebuilds `data/drops.js` without fetching anything.
- `drops.js` format: `items: { <meowDB item id>: { name, sub, icon } }`, `mobs: { <monster key>: [[itemId, score, osmlibPercent or null], ...] }`, best score first.

### Refreshing the data

1. Open https://meowdb.com/msclassic/world-map, open DevTools, paste [`tools/crawl_meowdb.js`](tools/crawl_meowdb.js) into the Console and press Enter. It walks every map reachable from Henesys, plus every world-map dot (that's how it finds Florina Beach, which you can only reach by NPC). It pauses 450 ms between requests and takes about 5 minutes. Then it downloads `meowdb-pack.json`.
2. Move that file to `data/raw/meowdb-pack.json`.
   - Monster sprites: after rebuilding, run `python3 tools/fetch_mob_images.py`. It only downloads monsters that don't have a file yet. meowDB serves many sprites as animated GIFs under a `.png` URL, so the script names files by their real format.
3. Run `python3 tools/build_data.py`.

How the crawler reads meowDB, in case meowDB changes its page format:
- Map pages are Next.js. The data is in the `self.__next_f.push([1,"..."])` chunks: join them, then brace-match the object that contains `"connectedMaps":[`.
- Monster stats come from each monster page's JSON-LD (`additionalProperty`), not the flight data.
- The world map's dots and edges are the `{"id":"VictoriaIsland","order"...}` object on `/msclassic/world-map`.

The pack format is documented at the top of `build_data.py`.

**Agent note:** a page on meowdb.com can't `fetch` or `POST` to `localhost`, because the browser blocks it. To move crawl data from the browser pane to disk, return it through the JS tool in chunks of about 27k characters, write them with the Write tool, and compare checksums.

### `victoria.js` format

```js
window.WORLD_DATA = {
  meta: { name, status: "meowdb", source, crawledAt, scale: 6 },
  regions: { henesys: { name: "Henesys" }, ... },      // from world-map town/area dots
  mobs: { m2: { name, level, hp, exp, def, mdef, acc, avoid, meowdbId, boss? }, ... },
  maps: [{
    id: "henesys",            // slug of the name; unique; used in links and #map=
    name, mapId: "010001000", // meowDB/game map ID, a STRING with leading zeros
    region, type, street,     // type: town | field | hidden | dungeon | safe | building | boss
    x, y,                     // world units (world is 3840 x 2800; sections sit below it)
    mobs: [{ id: "m2", count }], links: ["other_slug", ...],  // links are undirected, listed once
    verified: true,
    layer?: "underground", area?: "forgotten_hollow", section?: "<section id>",
    pinned?: true, worldMapDot?: true, exits?: [{ mapId, name, region }],  // exits = links off the island
  }],
  sections: [{ id, name, root, entry: { x, y }, stair?: false, portal?: { dx, dy }, label? }],
  routes: [],                 // boat/travel edges { from, to, kind, via, label }; none yet
};
```

The page merges `WORLD_TERRAIN` into this at load time (`DATA.islands`, `biomes`, `rivers`).

## How nodes are placed (`build_data.py`)

The game's own world map has 56 dots for Victoria Island. meowDB exposes their positions, and coordinates are dot × 6 (`SCALE`). The terrain was fitted to the same coordinates. Each map's position comes from the first rule that applies:

1. **In a section:** the section's tree layout (see below). Pins don't apply here.
2. **Pinned:** the position stored in the previous `victoria.js` with `"pinned": true`. Edit-mode drags set the pin.
   - **Catch:** `MANUAL_POS` at the top of `build_data.py` writes into the same table *after* the pins, so it wins over them. It holds hand-placed positions, by map name, for the Monkey Swamps and the Deep Forest / Damp Tree-Forest area. The values match the current pins, so nothing conflicts today. If you drag one of those maps, also update or remove its `MANUAL_POS` line.
3. **Kept:** any other map keeps its position from the previous `victoria.js`, so a rebuild never shuffles your layout. `python3 tools/build_data.py --relayout` skips this step.
4. **World-map dot:** placed exactly on its dot.
5. **Otherwise:** a small force simulation (numpy, 900 steps).
   - Links pull maps together; all maps push apart.
   - Each map is drawn gently toward its nearest dot, measured in link hops.
   - Links into a section are ignored.

Today, every island map is pinned or kept, so steps 4–5 only matter for new maps or `--relayout`.

### Node types

`node_type` in `build_data.py` sets each map's type from its meowDB street name and links:

- `boss`: every monster on the map is a boss (The Cursed Sanctuary).
- `town`: world-map town/area dots, plus hubs that open onto hunting maps, such as Sleepywood and Forgotten Hollow.
  - Towns that span several nodes get a light blue band around all their maps (`TOWN_GROUPS` and `drawTowns` in `js/map.js`). The band covers the convex hull of the town's maps with rounded edges, since a town's maps don't always link to each other. The list is hand-picked: Henesys (with Henesys Market and Henesys Park) and Kerning City (with Niora Hospital and the Subway Ticketing Booth).
- `hidden`: the street name says Hidden Street.
- `building`: no monsters and only one exit (shops, houses, saunas). Never drawn on the map. Each building's one linked map is its **host** (`hostOf` / `buildingsOf` in `js/map.js`): a town, or a spot like Henesys Market or Sleepywood Hotel. The host's panel lists its buildings under **Buildings**; clicking one opens it as a sub-pane (`panelSub`) with **← Back to <host>** and its connected maps. Selecting a building anywhere (search, a `#map=` link, a panel link) selects the host and opens that sub-pane. A monster search that matches a building rings its host.
- `safe`: no monsters but more than one exit.
- `dungeon`: the street is a Dungeon, Shallow/Deep Passage or Kerning City Subway. These also get `layer: "underground"` and sit on a generated dark cave backdrop.
- `field`: everything else.

### Areas

`AREAS` in `build_data.py` tags maps by ID prefix. Right now that's `forgotten_hollow` for `010006*` (27 maps). Tagged maps are hidden unless **Forgotten Hollow** is ticked. Jumping to one of them (search, a connected-map button, or a shared link) turns the toggle on (`reveal()` in `map.js`).

### Sections

A section cuts everything behind a root map off the island and draws it as a tree in its own dark panel below the island. Panels stack in the order they're listed in `SECTIONS`, and edges inside them are straight.

**Sleepywood Dungeon** (34 maps): the Hotel and its saunas, Sleepy Dungeon I–V, and the whole Ant Tunnel → Jr. Balrog line.
- It's a clean tree with a faint dashed staircase line from Sleepywood to the entrance marker.
- The only way into it from the surface is through Sleepywood.
- Its one link out is Sleepy Dungeon V ↔ Forgotten Dungeon Tunnel.

**Forgotten Hollow** (27 maps). The game links it to the island at two ends:
- **One end:** The Tree Tunnel At the Forest Up North (Ellinia) ↔ Forgotten Entrance III. That's the section root.
- **Other end:** Forgotten Dungeon Tunnel ↔ Sleepy Dungeon V.

How the panel is laid out:
- **Main line:** Forgotten Entrance III → … → Collision of Ice and Fire → Forgotten Dungeon Tunnel → The Faded Canopy. `align` puts Forgotten Dungeon Tunnel straight below Sleepy Dungeon V, so their link is a vertical line.
- **Loop:** Primeval Forest II → I → Forgotten Hollow town → The End of Fleeting Light → Perilous Descent → … → Another Sanctuary runs on the row below. The End of Fleeting Light ↔ The Faded Canopy closes the loop as a short vertical link.
- **Entrance:** The Tree Tunnel is far from the panel, so there's no staircase. A "↓ Forgotten Hollow" portal marker by The Tree Tunnel jumps to Forgotten Entrance III instead.
- **Toggle off:** the panel and the portal disappear (`sectionShown`).

`SECTIONS` options:

| Key | Meaning |
|---|---|
| `root` | Map the section hangs from. It stays on the island. |
| `exclude` | Root links that lead back to the surface; the walk skips them. |
| `start` | Walk only from these maps instead of all root links. |
| `area` | The section's own `AREAS` entry. The walk never enters other areas or earlier sections. |
| `spine` | Main line runs from the root to this map. Default: the longest branch. |
| `align: [member, other]` | Shift the panel so `member` sits straight below `other`. |
| `leaves_above` | Dead ends off the main line go above it. Shops always do. |
| `stair: False`, `portal: [dx, dy]`, `label` | Portal marker (offset from the root) instead of a staircase, and a short name for the entrance marker. |

Tree layout:
- A breadth-first tree is built from the root, at 125 world units per step.
- Each non-main branch takes the first free row below where it splits off, for its whole length.
- The build prints any links that don't fit the tree, and any links leaving the section.

On the page, a link from the root into its section is drawn from the panel's entrance marker, not from the root (`endpoint()` in `map.js`).

## Changing the layout

**Edit mode** (backtick key):
- Drag nodes to move them. Moved nodes become `pinned`. Click empty ground to copy its `"x": .., "y": ..`.
- Nothing is saved to disk automatically. A reload loses unsaved moves.
- To save, use **Download victoria.js** and replace `data/victoria.js`, or the route below.

**Saving from the browser without downloading.** This is how the user's hand layout was saved. Run this in the page:

```js
copy(JSON.stringify(Object.fromEntries(window.worldMap.DATA.maps.map(m => [m.id, [m.x, m.y, m.pinned ? 1 : 0]]))))
```

Paste the result into a file, then:

```bash
python3 tools/save_positions.py positions.json
```

It only changes `x`, `y` and `pinned`. An agent can run the same expression with the browser pane's JS tool, but should read from the user's tab without reloading it, because unsaved moves live only in that tab.

**For lasting hand placements in code**, add the map name and position to `MANUAL_POS`.

**Link bends:** each link curves slightly to one side, picked from a hash of its key (`edgeCurve`). To bend one the other way, add its key (the two map ids, sorted, joined by `|`) to `FLIP_BEND` in `js/map.js`. The Burnt Land III–IV and IV–V links are flipped so the run curves outward.

## `js/map.js` structure

Top to bottom:
1. **Difficulty colors:** `diffFor`, `diffBands`.
2. **Data indexes:** `byId`, monster helpers, `levelRange` / `farmRange` / `mapDiff`, and the `edges` + `neighbors` built from `links` and `routes`.
3. **State:** level and toggles saved in `localStorage`. `isVisible(m)` decides what's shown.
4. **Sections:** `endpoint`, `sectionShown`, `portalPos`, `sectionBox`, `drawSections`, `drawSectionMarkers`, `hitSectionEntry`.
5. **Terrain:** the island, biomes, river and decorations, built once into batched `Path2D`s. Scenery is scaled by `DS = scale / 3.75`, because it was first drawn for a smaller world.
6. **Drawing:**
   - Terrain, edges and caves are drawn in world space. Nodes, labels and edge dots are drawn in screen space, so they stay readable at any zoom.
   - Draw order: terrain → section plates → caves → town bands → edges → nodes → labels (see Labels above) → section markers → clouds → vignette.
   - The canvas only redraws when `needsDraw` is set.
7. **Camera:** `fitTarget` (the islands plus visible section panels), `animateTo`, `zoomAt`, `flyTo`.
8. **Input:** pointer pan, pinch and drag; `hitNode` falls back to section entrance and portal markers.
9. **Panel and HUD:** `select`, `renderPanel`, level controls, `reveal`, search, the edit bar, `dataJSON()` for export.

`window.worldMap = { DATA, state, cam, select }` is exposed for debugging and for the position dump above.

## Gotchas

- **Browser cache:** serve with `tools/serve.py` (sends `Cache-Control: no-cache`) so a normal reload gets edited files. Plain `python3 -m http.server` lets browsers reuse stale `map.js`/`terrain.js` until a hard refresh (Ctrl+Shift+R). The live site on GitHub Pages caches files for about 10 minutes, so a deploy can take that long to show on a normal reload. Check in a separate tab if the user is working in theirs.
- **Batched `Path2D`s need a `moveTo` before each `arc` / `ellipse`.** Without one, each shape is joined to the previous one with a straight line, and the whole batch fills as one giant zig-zag polygon. Tree shadows used to do this and drew diagonal bands across the island.
- **Decoration knobs:**
  - Amount per biome: `decor.density` in `data/terrain.js`. Perion's mesas are at 0.8.
  - Colors and outline weights: `DECOR_STYLES` and the `use(...)` calls in `buildDecor`.
  - Minimum spacing so shapes don't pile up: `DECOR_GAP`.
  - Outlines are kept close to the fill color on purpose, so decorations stay in the background.
- **Map IDs are strings** with leading zeros (`"010001000"`). Never treat them as numbers.
- **`links` in `victoria.js` are listed once per pair.** Build neighbors in both directions.
- **Edit mode on a section map:** dragging it works in the page, but the next build puts it back on the tree layout.

## Features

See [FEATURES.md](FEATURES.md) for the full list of features.

## TODO

Feature requests, in the order we plan to tackle them. Finished ones move to [FEATURES.md](FEATURES.md).

1. **Ranking map hits for farming spots (for both items and monsters, but simply rank by monster)**. Currently we highlight every map that has any instance of a monster when we search for monsters or items. Like, "Orange mushroom" will highlight 23 maps. And, "Pig's head" will highlight 16 maps. However, there are some maps that are a lot better than others for farming orange mushrooms / pig heads, and I think we could group most cases into 3 tiers (best, okay, meh). For implementation, there aren't that many monsters in the game so we can simply have a mapping of monster to groups of maps by tier.

OK. Let's add map tier list. In fact, for this one, we should add a feature to allow people to edit tiers locally but provide a default that we package with the site.
Similar to the location edit feature.

**Button on search dialog**

Could you create a button at the bottom of the search dialog that reads "Show map rankings"? It can go to the left of the Clear button.
The button should be greyed out and not interactible with nothing selected, but when at least one monster or item is selected, it should be available to be clicked.
If more than the cap of monsters are selected, just make it greyed out again, with mouseover text "too many monsters selected, max N". The cap N is the largest number of monsters that drop any single item, computed from the data (currently 15, Fragment of Magic), so picking any one item on its own always works. For the purposes of the cap, an item that is dropped by multiple monsters (like leather) should "include" both of those monsters in the count, as we will need to render them in the subdialog.

**Subdialog within search dialog**

Clicking on it should transition the dialog into a "subdialog" (in the information hierarchy its like "to the right" / "deeper" than the top-level search dialog), with a back button at the top to return to the search multi-select, outside of the "scrollable space" of the subdialog.

The rest of the subdialog, within a scrollable, will render full-width cards, one per monster in the selection that got us to this subdialog. In the subdialog, every selected Monster from the search bar is now shown in the subdialog, with a full width card per monster from the previous page's selection.

Any selected items should result in the monster that drops it showing up in the subdialog, but with the item included in the card as well. If multiple items that are dropped by the same monster were selected, include them all in the cards. If an item is dropped by multiple monsters, all of those monsters should be included.

On each card, the monster should be shown the left side of each card (we can re-use the search multiselect icons for this), and any items selected for that monster should be shown to the right side of the monster.

Then, on the right side of the card, the list of all maps that contain the monster in a vertical ranked list order, grouped by the ranking tiers: "best", "okay", "meh". Ranking tier buckets that are empty should still be rendered for editing purposes. Each list should have a few buttons on the right: one rightmost button to "click to drag" which allows reordering it relative to the other maps (including moving it into other tier buckets). The main button (to the left of "click to drag") is the "find in map" button. The "find in map" has weird behavior - it will "temporarily" close the modal dialog, and select the map in particular, as well as search-highlighting it. However, this should result in a "modified state" of the main UI where, in the top-left panel, the search bar is gone, and hidden streets and forgotten hollow are all force-shown, and the "edit layout" button is not present. Instead, it should render small text in the same manner as the "picked" thing, that says "Showing map for monster xyz". Underneath that text, it should have two buttons spaced vertically: a larger "Return to ranking" above a smaller button "exit ranking".

**Search behavior after the new tierlist**.

We should also add a new slider, under "labels", called "rankings to show". It should have the 3 tiers "best", "okay" and "meh" as options. Now, when deciding to highlight maps for monster and item search, we should *only* highlight the maps that are greater than or equal to the selected tier.

**Decisions (agreed)**

- Tier names are **best / okay / meh** everywhere (cards, slider, saved data).
- **Default rankings** (packaged with the site, e.g. `data/rankings.js`, generated by a script from `victoria.js`): for each monster, rank its maps by its share of the map's spawns (that monster's spawn count ÷ all monster spawns on the map; e.g. 20 Snails out of 67 spawns = 30%). Ties break by raw spawn count, then map name.
  - A monster on only 1 or 2 maps: all of them are **best**.
  - Otherwise the top 15% of its maps are **best**, the rest of the top 50% are **okay**, and the bottom half are **meh** (rounding up, so best always has at least one map). For example, 34 maps → 6 best, 11 okay, 17 meh.
- **Saving edits**: edits are saved in the browser (localStorage) and override the packaged default per monster. Each card has a "Reset to default" for that monster. A **Download all rankings** button sits at the bottom-left of the search dialog (the file replaces the packaged default, like Download victoria.js does for the layout).
- **What opens the rankings**: only picks from the dialog (monsters and items). Typed search text doesn't count, and NPC picks are ignored (they can't be killed).
- **"Find in map" mode**: forcing Hidden streets and Forgotten Hollow on is temporary; the user's own settings come back on exit and aren't saved over. "Return to ranking" reopens the subdialog at the same scroll position. "Exit ranking" closes the ranking view and keeps the picks.
- **Rankings slider** defaults to **okay** (most searches are cluttered today). A map stays highlighted if it passes the slider for *any* selected monster on it. Maps that new data adds (not yet in a saved or default ranking) land in **meh**.
- **Greyed-out button**: shown as disabled with a class/`aria-disabled` rather than the `disabled` attribute, since disabled buttons don't show a mouseover tooltip in most browsers.
- **Drag to reorder** uses pointer events (mouse and touch), not the browser's built-in drag-and-drop, which doesn't work on phones.
- **Same-name variants are ranked separately**, and the picker splits them too: today only Zombie Mushroom (Lv 24, `m21`, Ant Tunnels etc.) and a Lv 30 one (`m800011`, only Precipice of Darkness in Forgotten Hollow). The picker shows them as "Zombie Mushroom" and "Zombie Mushroom (Lv 30)"; the variant on the most maps keeps the plain name, the others get "(Lv N)". Each gets its own card, ranking and drops. Forgotten Hollow isn't released yet, so this data may be wrong. If the Lv 30 one turns out to be an instance-only monster (like the Lv 21 Ligators in the Kerning party quest), it should be left out of the picker altogether.
- **Card height**: each card's map list is a fixed height of 10 map rows and scrolls inside the card (Slime has 52 maps). Adjust if it looks awkward.

2. **Full screen map info dialog** view. Some of the minimaps are weird (tall/wide) and make the right hand pane a bit difficult to use. We should add a button in the right hand info panel above "minimap" that allows us to view a fullscreen dialog of all the info for the map. The dialog can contain the minimap as well as the same organized information in a similar way as the right hand panel.

## Known data quirks / ideas

- As of 2026-11-01, meowDB's map pages no longer embed the `"connectedMaps":[` object that `tools/crawl_meowdb.js` and `tools/scrape_minimaps.py` look for (portals, NPC positions and minimap sizes aren't in the page at all). Both crawlers will likely fail on maps they haven't saved yet until they're updated. Monster pages (JSON-LD stats) and `/msclassic/api/drops` still work.
- Utah's Pig Farm has a "Super Ribbon Pig" at level 200 (as listed on meowDB), so it always shows red.
- Florina Beach has no route link to the rest of the island (you reach it by NPC). `routes` supports boat or travel edges if one is wanted.
- "Leads off this map" in the panel lists links to maps outside Victoria Island (from `exits`).
- Possible next steps:
  - A damage-based difficulty check, using the HP and defense data.
  - Autosaving Edit-mode moves to `localStorage`.
  - More sections, such as the Kerning subway.
  - Other islands.
