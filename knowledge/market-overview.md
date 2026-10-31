# MapleStory Classic — Free Market Overview

Background knowledge on how the player-driven market works in MapleStory Classic. This is the foundation for any market-assistance tools built in this project.

## How trading works

- **No auction house.** There is no central, searchable marketplace in the game.
- **Player stores.** Players open a "store" at the spot where they are standing and stock it with any tradeable items.
- **Browsing.** A buyer has to walk up to a store and double-click it to open it, then scroll through its items.
- **Fixed prices.** Each item is listed at a fixed price set by the seller. There is no bidding or haggling inside the store.
- **Buying.** The buyer double-clicks an item to buy it instantly with their own mesos (the in-game currency).

## Store space

- Stores take up physical space on the map and **cannot overlap**.
- Each FM map fits only about **15–20 stores**.
- Finding a spot means going to a room and quickly switching through channels until one has space. If a room is full on all 40 channels, move on to the next room.

## Sales fee

- Every purchase has a **3% fee**, taken out before the mesos reach the seller. The game uses it to control inflation.
- Seller receives: `price × 0.97`.
- To net a target amount `N`, list at: `N / 0.97` (about `N × 1.0309`).
- Flipping (buying from one store and reselling) only makes a profit if `resale_price × 0.97 > purchase_price`.

## Where the market is

- The game has **4 cities**. The Free Market (FM) can be entered from **2** of them: **Henesys** and **Perion**.
- The FM has a **hub** map that leads to **20 market maps**, labelled "Free Market 1" through "Free Market 20".

### Hub layout

The entrances in the hub are arranged in 4 rows:

| Row | Markets |
|-----|---------|
| 1   | 1–6     |
| 2   | 7–12    |
| 3   | 13–16   |
| 4   | 17–20   |

- Players enter the hub from the **left** side.
- A quick **teleporter** moves players up between rows.
- So the entrances on the left of each row are the fastest to reach, along with FM 20.

### Prime (most-visited) market rooms

Because they are the fastest to reach from the hub entrance, these rooms are the most desirable:

**FM 1, 2, 7, 8, 13, 14, 17, 20**

These likely get the most foot traffic, which matters for both where to set up a store and where to look for listings.

## Channels

- The game has **40 channels**. Each channel is a full copy (instance) of the whole game world, so every map exists 40 times.
- Players change channel themselves. Changing channel usually **keeps them on the same map** and puts them at the nearest spawn point on that map in the new channel.
- This means a buyer can stay in, for example, FM 7 and quickly hop channel by channel to check every FM 7 copy.

## Scale of the market

- 20 market rooms × 40 channels = **800 separate free market areas**.
- Stores are spread across all 800 areas with no index, so finding the best price for an item means physically visiting stores. This search cost is the main problem market tools could help with.
