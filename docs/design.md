# Design: Market Listing Assistant

## Goal

Make it fast to post a just-opened in-game store to meowdb.com, with the right price, quantity and location on each listing. Price lookup is a smaller, later goal.

See `knowledge/` for background on the market and the websites.

## Decision: Chrome extension for meowdb, Python for the game side

**Chrome extension** (chosen) vs. **WebDriver / headless Chrome**:

| | Chrome extension | WebDriver / Playwright |
|---|---|---|
| Login | Uses the user's normal, already signed-in Chrome | Needs a separate signed-in profile. Google/Discord sign-in often blocks automated browsers |
| Bot detection | Normal browser, normal pace | Headless Chrome is easy to detect |
| Visibility | Fills forms in a visible tab, so the user can catch mistakes | Posts happen out of sight |
| Cost | Needs a way to pass data to and from Python | Everything stays in Python |

Fallback: Playwright with a saved, visible (not headless) Chrome profile, if meowdb's login works with it.

## Components

### 1. Python app (local)
- **Capture:** press a hotkey to screenshot the store window in the game. Screenshots only: never read game memory or send input to the game client, because of anti-cheat.
- **OCR:** read the item names, quantities and prices.
- **Name matching:** match each OCR'd name to the closest real item name from a list taken from meowdb or meso.watch. OCR names are often slightly wrong, so this step matters most.
- **Session location:** entered once per store session: channel, FM room, extra directions and in-game name.
- **Review table:** the user fixes and confirms the items before anything is posted.
- **Local server:** a small web server on localhost that hands out the confirmed list of items to post.

### 2. Chrome extension
- Gets the list of items to post from the local server.
- For each item, opens the item's meowdb page, clicks "Sell or buy this item", and fills in: Set price, price, quantity, Personal store, channel, room, directions and in-game name.
- A setting chooses whether it clicks Post itself or waits for the user to click. Start with the user clicking, and allow automatic posting once form-filling is reliable.
- Posts at a human pace.
- Later: mark old listings as sold out when the store closes.

### 3. Price lookup (later)
- Look up meso.watch prices and show them in the review table.

## Build order
1. Investigate meowdb: the Bulk buy / sell feature, how login works, and how the listing form's fields are built. Findings go in `knowledge/meowdb-site.md`.
2. Build the extension with items typed in by hand.
3. Add Python capture and OCR. This needs sample screenshots of the store window.
4. Add price lookup.
