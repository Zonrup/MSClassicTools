# meowdb.com — Site Investigation

Findings from looking at the site while logged out (2026-10-29). Items marked **TODO** need a logged-in session.

## General
- The site is now branded **NiaMeowDB** ("formerly MeowDB"). It covers many games; MapleStory Classic is under `/msclassic/`.
- Built with **Next.js** and served through **Cloudflare**.
- On 2026-10-29 a banner said the site was overloaded ("loading issues due to too many Maplers"), and item pages returned **ERROR 500**. Automation must handle errors and retry gently, without hammering the site.

## Login
- Page: `/msclassic/login`
- Options: **Continue with Discord**, **Continue with Google**, or email + password.
- The page shows a "Verifying you are human..." check (probably Cloudflare Turnstile).
- Conclusion: automated or headless browsers are a poor fit. The Chrome extension, running in the user's own signed-in browser, is the right approach.

## Useful URLs
| Page | URL |
|---|---|
| Free Market hub | `/msclassic/free-market` |
| Price Check | `/msclassic/price-check` |
| Deals | `/msclassic/free-market/deals` |
| Browse Listings | `/msclassic/free-market#browse-listings` |
| My Listings | `/msclassic/me/listings` |
| **Bulk buy / sell** | `/msclassic/me/listings?bulk=1` (needs login) |
| My Portfolio | `/msclassic/me/portfolio` |
| Price Alerts / Watchlist | `/msclassic/me/watchlist` |
| Safe to Sell? | `/msclassic/item-db/safe-to-sell` |
| Item DB | `/msclassic/item-db` |
| Item page | `/msclassic/item-db/{siteId}` (e.g. `/247` = Salad) |
| Item icon | `/msclassic/api/assets/icons/{gameItemId}` |

- **Two item IDs:** item pages use meowdb's own small numeric ID (e.g. 247), but icons use the game's item ID (Salad = 2020000). Matching OCR'd names to items needs a name → site ID lookup.

## meowdb has its own price data
- The Free Market page shows asking and sold prices (median, last 24h, or 7d/14d), and says it has 400k+ prices recorded from 75k+ player shop snapshots.
- So meowdb could also be a price source for the pricing step, not just meso.watch.

## Listing form (from the user's screenshot)
See `websites-and-selling-workflow.md` for the full field list.

## TODO (needs login and a working site)
- See what Bulk buy / sell (`/me/listings?bulk=1`) accepts: typed text, screenshots, or both, and whether one location applies to all items.
- Inspect the single-item form's HTML (field names, how the buttons work, React-controlled inputs) to plan how the extension fills it in.
- See what request "Post SELL listing" sends (in DevTools' Network tab), and what My Listings allows (edit, mark sold, delete).
