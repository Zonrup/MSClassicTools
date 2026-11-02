# Features

What the Victoria Island world map does, written as behaviors you can check. See `README.md` for how each one works and the open TODOs.

## Recently added

### Item and crafting station search
- Typing an ETC item's name in the search box (e.g. "tree branch") rings the maps of every monster that drops it. The Typed row under the search bar says which monsters drop it ("Tree Branch (from Stump, Dark Stump) · 44 maps").
- Drops come from meowDB's community drop lists: ETC items with a vote score of 3 or more. Equips and USE items are left out.
- Crafting stations are found by name or by craft: "smithing" finds the Anvil, "tailoring" the Sewing Machine, "arcforge" the Arcane Station.
- "crafting station" rings all six station types together, even though that's more than the usual limit of three matches.
- Station NPCs show their craft in the side panel's NPC list (e.g. "Smithing station").

### Monster drops on hover
- Hovering a monster card in the "Find anything" picker shows a popup with its level, difficulty, map count and common drops, each with its icon and item type.
- Hovering a monster row in a map's side panel shows the same popup, to the left of the row.
- Drops show OSMLib's reference rate where known (e.g. Stump: Tree Branch 40%).
- Monsters with no recorded drops say "No common ETC drops recorded".
- The picker's filter also matches drop names: "branch" shows the Stump cards.

### Picker "Selected" chips
- Picked monsters show as chips at the top of the picker, each with its sprite.
- × on a chip unpicks that monster: its card loses its check mark and its maps lose their rings.

### Typed and Picked rows under the search bar
- The box under the search bar has a **Typed** row (what the typing matches) and a **Picked** row (the picker's selection), each shown only when it has something.
- Each row's × clears only that row.
- Typed matches and picks ring their maps together, so the rings always match what the rows list. (Before, typing an NPC's name kept the picks ringed with no sign of why.)
- Typing that matches nothing says "No matches".

### Selected entries in the map tooltip
- While anything is typed or picked, hovering a map adds a light blue section listing which of the selected monsters, items and NPCs are on that map or in its buildings.
- Each item is listed under the monster there that drops it, e.g. "Stump" with "• Tree Branch".
- Selected NPCs show with an "NPC" tag (e.g. hovering Ellinia with "arwen the" typed shows "Arwen the Fairy").
- Maps with none of the selection show the plain tooltip.

### Selected entries in the side panel
- With a map open, monster rows that are typed or picked get a light teal highlight, matching their rings on the world map.
- A monster that drops a typed item is marked too, with a "Drops <item>" line under its stats (e.g. Stump: "Drops Tree Branch").
- NPC rows matching the typed search are marked in the same teal, including NPCs inside the map's buildings, and so are their minimap dots (and the pin of a building holding one).
- On the world map, every search hit (monster, item or NPC) gets the same teal ring; NPC rings used to be yellow.
- The marks update live as the typing or picks change, and clear with them.

### Town outline
- Towns that span several nodes sit inside one light blue band, so they read as one town:
  - Henesys, with Henesys Market and Henesys Park;
  - Kerning City, with Niora Hospital and the Subway Ticketing Booth.
- The band is one rounded blob covering the area between the town's maps, even where they don't link to each other.
- Links, nodes and labels draw on top of the band.

### Missing maps added
- **Cabin of the Forsaken** shows as a hidden street off The Murky Swamp II, with a skull badge for its boss, Shade (Lv 48). Its panel lists Shade, and "shade" in the search box rings it.
- The Murky Swamp II's panel links to the Cabin by name, where it used to show an unnamed "Leads off this map" entry.
- **Magic Library** shows as a safe zone next to Ellinia, with **The Circulation Desk** as its building. Opening the desk shows "← Back to Magic Library" and its NPCs: Lyn the Librarian, Sabrina the Scribe and Jon the Justicar.
- Searching any of those three NPCs rings the Magic Library.

### Picker tabs: monsters, NPCs and items
- The picker has three tabs below its filter box (which sits under the Selected chips), in this order: **Monsters**, **NPCs** and **Items**, each with its count of matching entries.
- NPC cards show where the NPC is (or a station's craft); item cards show the item's icon and which monsters drop it.
- Picks from every tab show as Selected chips (each × removes it), in the Picked row under the search bar, and as a ✓ count on their tab.
- Picked NPCs ring their maps; picked items ring every map of the monsters that drop them. Several items can be picked at once, e.g. Tree Branch and Leather: hovering Forest West of Henesys then shows "Stump • Tree Branch", "Pig • Leather" and "Ribbon Pig • Leather", and its side panel marks those three monsters.
- With filter text, tabs with no match are greyed out but can still be opened; their grid says "No matching …".
- Each edit of the filter text switches to the first tab with a match when the open tab has none: "lyn" jumps to NPCs, while "branch" stays on Monsters (Stumps drop branches).

## Pre-existing features

### The map
- Every Victoria Island map (248, from meowDB) is a node on a hand-drawn island, in the style of the in-game world map, with biomes, trees, rocks, clouds and curved paths.
- Node shapes show the map type: towns (blue, with a name banner), fields, hidden streets, dungeons and underground maps (on a dark cave backdrop). Boss maps get a skull badge. Buildings (shops, halls, saunas) aren't drawn.
- Sleepywood Dungeon and Forgotten Hollow are drawn as separate dark panels below the island, laid out as trees.
  - Sleepywood Dungeon has a dashed "staircase" line up to Sleepywood.
  - Forgotten Hollow has a "↓ Forgotten Hollow" portal marker by The Tree Tunnel that jumps to its entrance.
- Florina Beach is drawn as its own small island.

### Difficulty colors
- Your level (number box and slider, top left) colors every map and monster: red (too hard), orange (hard), yellow (good farming), green (easy), grey (trivial).
- The color cut-offs widen as your level rises; the legend (bottom left) shows the current level ranges.
- A map's color comes from the level a third of its spawns are at or above, so a few strong monsters aren't hidden by many weak ones. Bosses don't count unless the map has nothing else.
- Map labels show each map's level range.

### Moving around
- Drag to pan; scroll wheel or pinch to zoom; `+` / `-` keys or the + / − buttons to zoom.
- `Home` or the ⤢ button fits the whole island and visible sections.
- Clicking a map flies the camera to it.

### Labels
- The Labels slider has three modes: None (only the hovered or selected map and search hits), Smart and All.
- Smart shows more labels as you zoom in: town banners only, then area names, then main-road maps, then every map.
- Smart labels never overlap each other, nodes, section markers or the HUD cards.
- Numbered runs (e.g. "East Rocky Mountain I–VII") get one tilted, italic area name when zoomed out. Some hand-picked areas, like Golem Temple, get one too.

### Side panel
- Clicking a map opens a panel on the right with:
  - its type, a "✓ meowDB" badge, street, region and a link to its meowDB page;
  - its level range and difficulty at your level;
  - its minimap;
  - its monsters, with level, HP, EXP, spawn count and difficulty;
  - its buildings, connected maps and NPCs;
  - "Leads off this map" links for exits that leave Victoria Island.
- `Esc` or × closes the panel.
- The URL keeps the selected map (`#map=<id>`), so a link opens that map directly.
- Buildings open as a sub-pane of their host map, with "← Back to <host>". Selecting a building anywhere (search, link, panel) opens its host with the building's sub-pane.

### Minimap
- The minimap shows a pin for each portal. Clicking a pin opens the map it leads to; pins to maps off the island link to meowDB.
- Hovering a pin labels it and lights every pin leading to the same map, and rings that map on the world map.
- Hovering a map node on the world map lights the minimap pins that lead to it.
- NPCs show as dots on the minimap.
- Hovering or clicking a connected map, building or NPC row lights its pin or dot. Clicking keeps it lit and scrolls the minimap into view; clicking a lit building or map row opens it.

### Search
- Typing in the search box, or anywhere on the map, searches monsters, NPCs and maps by the start of their name (maps also ignoring a leading "The"), from 2 characters on.
- When 3 or fewer monsters (or NPCs) match, their maps get teal rings as you type; with more, the hint says to keep typing.
- Enter: an exact map name opens that map; otherwise the camera zooms to the ringed maps; otherwise it opens the first matching map.
- `Esc` on the map clears the typing, then the picks.
- A monster or NPC inside a building rings the building's host map.

### "Find anything" picker
- The mushroom button next to the search box opens a dialog of monster cards sorted by level: sprite, name in its difficulty color, level(s) and map count. Same-name variants (like the two Zombie Mushroom levels) are merged.
- Click cards to pick any number; their maps get rings live. "Show on map" closes the dialog and zooms to them; "Clear" unpicks all.
- The filter box narrows the cards and shows map-name chips that jump to that map.
- Opening it from the keyboard (type, Tab, Enter) starts the filter with the typed text.

### Map tooltip
- Hovering a map shows its name, plus its level range and difficulty, or "Town".

### Settings
- The Hidden streets and Forgotten Hollow toggles show or hide those maps. Jumping to a hidden map (search, link, panel) turns its toggle back on.
- Level, toggles and label mode are saved in the browser and come back on the next visit.

### Edit layout
- Backtick (`` ` ``) or the Edit layout button turns on Edit mode. Nodes can be dragged; moved nodes are marked as pinned.
- Clicking empty ground shows and copies its coordinates.
- "Copy data JSON" and "Download victoria.js" export the edited layout. Nothing is saved automatically.

### Data and tools
- Map, monster, minimap, NPC and drop data come from meowDB, via the scripts in `tools/`.
- `tools/serve.py` serves the page locally with caching turned off, so a normal reload shows edits.
- `tools/deploy_pages.py` publishes the page to liujason.me/msclassicatlas.
