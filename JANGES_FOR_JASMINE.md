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
- **Occasion:** default `everyday`, chosen from the 8 options (see the second Sunday update below).

**Item picker** (`pick-item`). Two sources: the catalog and "From my closet" (the profile's `closet`), plus a "No anchor" choice. Filter the catalog to the profile's `departments` plus unisex items.

**Outfits** (`outfits`). Show `owned` pieces in each outfit card, marked "from your closet" with no price. They have no swaps. The anchor never has swaps either.

**Try-on** (`tryon/[outfitId]`). `TryOnRequest.item_ids` takes catalog ids only. If the anchor is owned, the user's photo may already show it. Decide whether to ask Gemini to keep that garment as it is.

**Checkout** (`checkout/`). The cart is `Outfit.items` only, never `owned`. Default the mandate limit to `budget_max`.

**Payments: Stripe instead of a Visa sandbox.** Visa has no open sandbox for agent payment tokens, so checkout runs on Stripe Issuing in Stripe's sandbox. You don't need to ask the Visa team about one anymore. `/checkout/mandate` creates a virtual card with the mandate's limit and clothing-only categories, and `/checkout/confirm` makes a simulated purchase on it, which Stripe declines if it's over the limit. Before building it, check that Issuing works on a sandbox account: create one card with a test key and confirm its brand is Visa. If it doesn't, keep the mandate in our code only and label the payment as simulated. The app needs no Stripe SDK; only `CardRef.label`'s value changes, to the Issuing card's last four digits. Section 8 of [PLAN.md](PLAN.md) has the details.

**Rate** (`(tabs)/rate`). `RatePair.request` is an `OutfitsRequest`, so it now shows a budget range and possibly an owned anchor or no anchor. Only the display changes.

## Stretch goal that will touch the app later

Closet items as candidates, not only as the anchor ("you already own shoes that work"). The model would be allowed to pick owned pieces anywhere in an outfit. `Outfit.owned` already carries them, so if the Outfits card renders `owned` generally (not only for the anchor), nothing changes on your side when this lands.

## Not changed

The scan (`/scan`, `/faces/find-owner`), `/tryon`'s response, `/checkout/cart` and `/checkout/confirm`, `RateChoice`, `DELETE /me`, and the timeline's integration checkpoints (Sat 10 PM, Sun 6 AM).

## Update, Sunday Oct 18

Your three change requests in [CHANGES_FOR_CHARLIE.md](CHANGES_FOR_CHARLIE.md) are in, and the contract got stricter. `types.ts` and `schemas.py` already match.

| Type | Change |
| --- | --- |
| `StyleProfile` | `formality` is removed |
| `OutfitsRequest` | New optional `upgrade_of: string[] \| null` for "make it nicer": the ids of the current outfit's `items` and `owned`. `/outfits` then returns one pricier outfit, in the range (that outfit's total, total + $150], which may go past `budget_max`. `makeItNicer(req, outfit)` in `client.ts` sends it when mocks are off. The backend rejects `budget_min` below 0 or above `budget_max`, and `max_item_price` of 0 or less, with a 422 |
| `Anchor` | Now a union: `{ source: 'catalog', id }` or `{ source: 'closet', id: ClosetId }`. An id that isn't in the catalog or the user's closet is a 422 |
| `ClosetItem` | `id` is typed `ClosetId` (`closet_<n>`) |
| `Outfit` | `id` is opaque, because the backend doesn't store outfits. `items` includes a catalog anchor. `total` is computed by the backend and rounded to cents. After a swap, keep looking up swaps under the original item's id |
| `OutfitsResponse` | `outfits` holds 1 to 3 (normally 2 or 3), never 0: when every generator fails, `/outfits` returns a 503. `generated_by` covers every outfit in the response |
| `/fit` | Removed, with `FitFeedback`, `ItemFit`, `FitRating` and the `fit/[orderId]` screen |

**Vocabularies.** Replaced by the second Sunday update below.

**Catalog.** The first pull has 930 real products from 21 stores, each with `url` set to its own product page. They still need tagging before `/catalog` can serve them.

## Update 2, Sunday Oct 18 (after merging your Supabase and try-on work)

The vocabulary and the occasions were reworked, so the contract changed again. `types.ts`, `schemas.py`, `session.tsx`'s `OCCASIONS` and the mocks already match, and the app typechecks.

| Type | Change |
| --- | --- |
| `Occasion` | 8 options instead of 14: `formal`, `semi-formal`, `work`, `everyday`, `party`, `casual`, `athletic`, `comfy`. `date`, `active`, `wedding_guest`, `interview`, `brunch`, `travel`, `concert`, `outdoors`, `campus` and `lounge` are gone |
| `Pattern`, `Fit` | **New.** `Pattern` is `solid`, `stripe`, `check`, `small-print`, `large-print` or `graphic`. `Fit` is `slim`, `regular`, `relaxed` or `oversized` |
| `CatalogItem` | New `pattern: Pattern` and `fit: Fit \| null` (`null` for shoes and accessories) |
| `ClosetItem` | New `pattern`, `fit` and `season`, the same as `CatalogItem` |
| `StyleProfile` | New `fits: Fit[]`: the fits the user wears. Retrieval and the reward prefer items with one of them. Showing or editing it on "Your style" is your call |

**Vocabularies,** final in `training/vocab.py` and listed in PLAN.md section 5:

- **Colors (25):** white, cream, beige, tan, khaki, brown, gray, charcoal, black, navy, denim, olive, blue, forest-green, muted-green, burgundy, light-blue, lilac, gold, silver, yellow, orange, red, pink, purple. `swatches` has all of them. Plain `green` is gone; the mock Stan Smiths are now `forest-green`.
- **Style tags (17, 1 to 3 per item):** minimal, old-money, western, preppy, streetwear, techwear, workwear, outdoors, athleisure, bohemian, y2k, goth, coastal, sporty, clean-girl, soft-girl, grunge. Old tags like `relaxed`, `smart-casual` and `logos` are gone; `avoid` examples are now things like `y2k` or `orange`.

**Mocks.** I kept your 18 real products and gave them `pattern` and `fit`: the `item()` helper defaults to `solid` and `regular` (`null` for shoes and accessories), with `relaxed` or `oversized` on the wide-leg pant, hoodie and baggy jeans, and `graphic` on the Brain Dead tote.

**Catalog.** `training/catalog.json` isn't committed yet, so `/tryon` still reads `catalog_raw.json`. It lands once the whole catalog is tagged with the new vocab, and it will include your 18 mock ids.
