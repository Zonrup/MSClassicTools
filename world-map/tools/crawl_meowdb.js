// Crawl Victoria Island map + monster data from meowDB.
//
// How to run: open https://meowdb.com/msclassic/world-map in a browser, open DevTools,
// paste this whole file into the Console and press Enter. It pauses between requests
// to go easy on the site, and takes a few minutes. When it finishes it downloads
// meowdb-pack.json. Put it in world-map/data/raw/ and run:
//   python tools/build_data.py
//
// It reads the data the site embeds in each page (Next.js flight data and JSON-LD),
// so it breaks if meowDB changes its page format.
(async () => {
  const DELAY_MS = 450;
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

  // Join the Next.js flight chunks embedded in a page into one string.
  async function flight(path) {
    const res = await fetch(path);
    if (!res.ok) throw new Error(`HTTP ${res.status} for ${path}`);
    const html = await res.text();
    const rsc = [...html.matchAll(/self\.__next_f\.push\(\[1,"((?:[^"\\]|\\.)*)"\]\)/g)]
      .map((m) => JSON.parse('"' + m[1] + '"')).join("");
    return { html, rsc };
  }

  // Parse the JSON object that starts at index i (string-aware brace matching).
  function objectAt(s, i) {
    let d = 0, inStr = false, j = i;
    for (; j < s.length; j++) {
      const c = s[j];
      if (inStr) { if (c === "\\") { j++; continue; } if (c === '"') inStr = false; continue; }
      if (c === '"') inStr = true;
      else if (c === "{") d++;
      else if (c === "}") { d--; if (d === 0) break; }
    }
    return JSON.parse(s.slice(i, j + 1));
  }

  // The object that contains `key`, found by walking back to its opening brace.
  function objectAround(s, key) {
    const k = s.indexOf(key);
    if (k < 0) return null;
    let depth = 0, i = k;
    for (; i >= 0; i--) {
      const c = s[i];
      if (c === "}") depth++;
      else if (c === "{") { if (depth === 0) break; depth--; }
    }
    return objectAt(s, i);
  }

  async function retry(fn) {
    for (let attempt = 0; ; attempt++) {
      try { return await fn(); } catch (e) {
        if (attempt >= 2) throw e;
        console.warn(e, "retrying");
        await sleep(3000 * (attempt + 1));
      }
    }
  }

  // 1. The game's world map dots for Victoria Island.
  const { rsc: wm } = await flight("/msclassic/world-map");
  const at = wm.indexOf('{"id":"VictoriaIsland","order"');
  const worldmap = objectAt(wm, at);
  console.log(`world map: ${worldmap.spots.length} dots`);

  // 2. Breadth-first crawl of maps, starting from Henesys and every world-map dot
  //    (Florina Beach is only reachable by NPC, so the dots are needed to find it).
  const maps = {}, outside = {}, errors = {};
  const queue = ["010001000", ...worldmap.spots.map((s) => s.mapId)];
  const seen = new Set(queue);
  while (queue.length) {
    const id = queue.shift();
    let m;
    try {
      m = await retry(async () => objectAround((await flight(`/msclassic/maps/${id}`)).rsc, '"connectedMaps":['));
    } catch (e) { errors[id] = String(e); continue; }
    if (!m) { errors[id] = "no map data"; continue; }
    const slim = {
      id: m.id, name: m.name, street: m.streetName, region: m.region, isTown: m.isTown, returnMap: m.returnMap,
      links: (m.connectedMaps || []).map((c) => c.mapId),
      mobs: (m.monsters || []).map((x) => ({ id: x.id, name: x.name, count: x.count, respawnMin: x.respawnMin, respawnMax: x.respawnMax })),
      portals: (m.portals || []).map((p) => ({ type: p.type, to: p.toMapId, x: p.x, y: p.y })),
      total: m.totalMobCount, mobRate: m.mobRate,
    };
    if (m.region !== "VictoriaIsland") outside[id] = slim;
    else {
      maps[id] = slim;
      for (const n of slim.links) if (!seen.has(n)) { seen.add(n); queue.push(n); }
    }
    if (Object.keys(maps).length % 25 === 0) console.log(`maps: ${Object.keys(maps).length}, queued: ${queue.length}`);
    await sleep(DELAY_MS);
  }

  // 3. Monster stats from each monster page's JSON-LD.
  const mobIds = [...new Set(Object.values(maps).flatMap((m) => m.mobs.map((x) => x.id)))];
  const mobs = {};
  for (const id of mobIds) {
    try {
      mobs[id] = await retry(async () => {
        const { html } = await flight(`/msclassic/monsters/${id}`);
        const doc = new DOMParser().parseFromString(html, "text/html");
        const out = { id, name: null, boss: /\\?"isBoss\\?":true/.test(html), props: {} };
        for (const s of doc.querySelectorAll('script[type="application/ld+json"]')) {
          try {
            const j = JSON.parse(s.textContent);
            if (j.additionalProperty) { out.name = j.name; for (const p of j.additionalProperty) out.props[p.name] = p.value; }
          } catch (_) { /* not the one */ }
        }
        return out;
      });
    } catch (e) { errors["mob:" + id] = String(e); }
    await sleep(DELAY_MS);
  }

  // 4. Pack into the compact format tools/build_data.py reads, and download it.
  const pack = {
    crawledAt: new Date().toISOString(),
    spots: worldmap.spots.map((s) => [s.mapId, s.x, s.y, s.type, s.title, s.levelMin, s.levelMax, s.mapCount]),
    wmEdges: worldmap.edges,
    maps: Object.fromEntries(Object.entries(maps).map(([k, m]) => [k, {
      n: m.name, s: m.street, t: m.isTown ? 1 : 0, l: m.links,
      m: m.mobs.map((x) => [+x.id, x.count, x.respawnMin || 0]),
      p: m.portals.filter((p) => p.to && p.to !== "999999999").map((p) => [p.to, p.x]),
    }])),
    outside: Object.fromEntries(Object.entries(outside).map(([k, m]) => [k, { n: m.name, r: m.region }])),
    mobs: Object.fromEntries(Object.entries(mobs).map(([k, m]) => {
      const p = m.props;
      return [k, [m.name, m.boss ? 1 : 0, p.Level, p.HP, p.EXP, p["Physical Defense"], p["Magic Defense"], p.Accuracy, p.Avoidability]];
    })),
  };
  const a = document.createElement("a");
  a.href = URL.createObjectURL(new Blob([JSON.stringify(pack)], { type: "application/json" }));
  a.download = "meowdb-pack.json";
  a.click();
  console.log(`done: ${Object.keys(maps).length} maps, ${Object.keys(mobs).length} monsters, errors:`, errors);
})();
