# Market Websites and Selling Workflow

## Websites

### meso.watch
- Estimates market prices from sales.
- Gets its data by scraping streamers' streams and running OCR on store windows that are open on stream.
- Sold items that haven't been collected yet still show in a store, faded and greyed out but readable. meso.watch uses these to record recent sales.
- Has a fast item search and links to the matching meowdb pages.

### meowdb.com
- Board where players post their own buy and sell listings. It only covers what players choose to post, so it is incomplete.
- Requires login to post. Contact details are only visible to logged-in users.
- No public API.
- Each item page has a "For sale and wanted" section with a "Sell or buy this item" button that opens the listing form:
  - **I want to sell / I want to buy**
  - Pricing mode: **Set price**, **Taking offers**, or **Trade**. Set price uses a "Price each (mesos)" field and an "Also accept offers" checkbox.
  - **Quantity**
  - Trade method: **Personal store** or **Direct trade**
  - **Channel**
  - **Where is your store?** (for example "Free Market room 13")
  - **Extra directions** (optional, for example `2nd floor left: "equips, scrolls"`)
  - **In-game name**, **Discord contact** (optional)
  - Usual playtime (optional), optional note
  - **Post SELL listing** button
- Listings show their price, quantity, total, channel and location, the trader's contact, and buttons to mark one Sold out or Not there.
- Has a **"Bulk buy / sell"** feature: "Type items or import screenshots".

## Current selling workflow

1. Find a store spot: check FM 1, 7 and 13, switching through channels. A spot usually turns up in 7 or 13.
2. Price each item using meso.watch's estimate, plus current meowdb listings.
3. Set up the in-game store with those prices.
4. Post each item to meowdb with its location (channel, room, directions). This is done by hand, one item at a time, and is the step that most needs automating.
