# Janges for Jasmine

Plan changes from Saturday Oct 17 that affect the app, the API contract or your endpoints. [PLAN.md](PLAN.md) has the full detail, and [src/api/types.ts](src/api/types.ts) and [backend/schemas.py](backend/schemas.py) already match everything below. Build any mocks from those files.

## Summary

1. The anchor is optional, and it can be a piece the user already owns (from their closet), not only a catalog item.
2. The budget is a range with a minimum and a maximum, plus an optional max price per item.
3. There are 14 occasions instead of 6.
4. Catalog items and profiles have a department (men's, women's, unisex).
5. The catalog grows from 50–80 to about 1,000 products. Nothing about it changes for the app except that there's more to browse.
6. Checkout runs on Stripe Issuing in Stripe's sandbox, since Visa has no sandbox of its own. The API shape doesn't change.

## API contract changes

| Type | Change |
| --- | --- |
| `CatalogItem` | New `department: 'men' \| 'women' \| 'unisex'` |
| `ClosetItem` | **New.** A garment the user owns, tagged from their photos: `id` (`closet_<n>`), `description` ("navy oxford shirt"), `slot`, `colors`, `formality`, `style_tags`, `photo_id` (the asset id of the photo it came from) |
| `StyleProfile` | New `departments: ('men' \| 'women')[]` and `closet: ClosetItem[]`. Both come back from `GET`/`POST /profile` and can be edited through `PUT /profile` |
| `Anchor` | **New.** `{ source: 'catalog' \| 'closet', id }` |
| `OutfitsRequest` | `anchor_id` is replaced by `anchor: Anchor \| null`. `budget` is replaced by `budget_min` and `budget_max`. New optional `max_item_price`. The rest is unchanged |
| `Occasion` | Adds `wedding_guest`, `interview`, `brunch`, `travel`, `concert`, `outdoors`, `campus`, `lounge` |
| `Outfit` | New `owned: ClosetItem[]`: pieces from the user's closet, which are free and never go in the cart. `items` is now only what would be bought, and `total` sums `items` only |
| `MandateRequest` | Unchanged, but the app should default `limit` to the request's `budget_max` |
| `Receipt` | New `authorization_id: string \| null`: Stripe's ID for the purchase. `null` means the payment was simulated (the fallback), so label it that way |

## Screens

**Your style** (`(tabs)/style`). Show the closet, the garments found in the user's photos, next to the summary and looks. The user can remove a wrongly tagged garment. Removing one is a `PUT /profile` with the item left out of `closet`.

**Build** (`(tabs)/build`). Everything is prefilled, so one tap builds outfits:

- **Anchor:** optional. Show the suggested one (the catalog item that best matches the user's style, chosen with some randomness) with a way to change or clear it.
- **Budget:** a slider with two handles, a minimum and a maximum. Default $50–$200.
- **Max price per item:** optional. The API and backend support it either way. Whether the Build screen shows a control for it, and where, is your call. It could be a stretch goal.
- **Occasion:** default `everyday`, chosen from the 14 options.

**Item picker** (`pick-item`). Two sources: the catalog and "From my closet" (the profile's `closet`), plus a "No anchor" choice. Filter the catalog to the profile's `departments` plus unisex items.

**Outfits** (`outfits`). Show `owned` pieces in each outfit card, marked "from your closet" with no price. They have no swaps. The anchor never has swaps either.

**Try-on** (`tryon/[outfitId]`). `TryOnRequest.item_ids` takes catalog ids only. If the anchor is owned, the user's photo may already show it. Decide whether to ask Gemini to keep that garment as it is.

**Checkout** (`checkout/`). The cart is `Outfit.items` only, never `owned`. Default the mandate limit to `budget_max`.

**Payments: Stripe instead of a Visa sandbox.** Visa has no open sandbox for agent payment tokens, so checkout runs on Stripe Issuing in Stripe's sandbox. You don't need to ask the Visa team about one anymore. `/checkout/mandate` creates a virtual card with the mandate's limit and clothing-only categories, and `/checkout/confirm` makes a simulated purchase on it, which Stripe declines if it's over the limit. Before building it, check that Issuing works on a sandbox account: create one card with a test key and confirm its brand is Visa. If it doesn't, keep the mandate in our code only and label the payment as simulated. The app needs no Stripe SDK; only `CardRef.label`'s value changes, to the Issuing card's last four digits. Section 8 of [PLAN.md](PLAN.md) has the details.

**Rate** (`(tabs)/rate`). `RatePair.request` is an `OutfitsRequest`, so it now shows a budget range and possibly an owned anchor or no anchor. Only the display changes.

## Stretch goal that will touch the app later

Closet items as candidates, not only as the anchor ("you already own shoes that work"). The model would be allowed to pick owned pieces anywhere in an outfit. `Outfit.owned` already carries them, so if the Outfits card renders `owned` generally (not only for the anchor), nothing changes on your side when this lands.

## Not changed

The scan (`/scan`, `/faces/find-owner`), `/tryon`'s response, `/checkout/cart` and `/checkout/confirm`, `RateChoice`, `/fit`, `DELETE /me`, and the timeline's integration checkpoints (Sat 10 PM, Sun 6 AM).
