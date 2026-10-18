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

**Catalog.** `training/catalog.json` is tagged and committed: 1,040 items from 24 stores, including your 18 mock ids, so `/tryon` reads it now. Three formal-wear stores were added (Jack Victor, Paul Evans, Mac Duggal), and `formal` now means formality 4–5, the same as `semi-formal`.

## Update 3, Sunday Oct 18 (after merging your accounts and Your style work)

Your branch merged with no conflicts. One change touches your code: nothing in the app called `POST /profile`, so with mocks off a new account finished onboarding with no profile (`GET /profile` answered 404 and Your style was empty).

- **`client.ts`:** new `createProfile(photos)`, which sends `{ photos: [{ id, base64 }] }` to `POST /profile`. On mocks it returns `mocks.profile`.
- **`onboarding/photos.tsx`:** "Next: your style" now sends the 30 newest outfit photos to `createProfile` (the route's maximum), puts the result in the session with `setProfile`, and only then calls `markOnboarded` and opens Your style. The link reads "Reading your style…" while it waits (Gemini takes a few seconds). If the call fails, the error shows on the screen and onboarding isn't marked done, so tapping again retries.

Open questions, your call:

- With zero outfit photos, the backend's "Send at least one photo" error shows. A friendlier message, or hiding the link until the scan finds a photo, would be nicer.
- The suggested anchor is only picked when the session first loads a profile, so right after onboarding Build has no anchor prefilled.

## Update 4, Sunday Oct 18, 06:30: your next few hours

[PLAN.md](PLAN.md) was rewritten from the current code; [section 10](PLAN.md#10-who-does-what-and-when) has the full timeline for both of us. Feature freeze is now about **11:00**, submit by **11:30**. Charlie is on the model until then, so everything below is yours.

| When | What | Details |
| --- | --- | --- |
| 6:30–7:15 | **Pick photos** | The system picker (`expo-image-picker`, multi-select) as the second option on the photos screen. No library permission and no face matching. Shrink each pick with the scan's thumbnail code (`makeThumb` in `src/lib/photos.ts` takes a media-library asset, so you may need a small variant for a picker URI), then call `createProfile` like "Next: your style" does, at most 30 photos. [PLAN section 3](PLAN.md#getting-your-photos) |
| 6:30–7:15 | **Checkout, fallback path** | The three routes in `backend/routes/checkout.py` return 501 today, so checkout only works on mocks. Build them without Stripe first: mandate stored with `supabase.create_mandate` and the fixed card label `Visa •••• 4242, agent card`; `/checkout/cart` checks the total from catalog prices against `limit − spent` and refuses "expired", "not_apparel" or "over_limit" with a suggestion; `/checkout/confirm` reruns the check, adds to `spent`, returns the receipt with `authorization_id: null`. That makes the "make it nicer → refused" demo real. [PLAN section 8](PLAN.md#8-trust-privacy-and-checkout) |
| 7:15–8:30 | **Stripe Issuing on top** | Still planned. First check that the sandbox account can create an Issuing card by API and that its brand is Visa; if not, the fallback ships as is. The steps are in `backend/services/stripe_issuing.py` and PLAN section 8. |
| 7:15–8:30 | **Supabase dashboard** | "Confirm email" off, "Allow manual linking" on, and the `feedback` and `mandates` tables from `backend/supabase_schema.sql` exist. |
| 8:30–9:30 | **The whole demo path, mocks off, on a real phone** | `EXPO_PUBLIC_USE_MOCKS=false`, backend running on the laptop (`npx expo start --tunnel` if venue Wi-Fi blocks it). Welcome → photos → Your style → Build → Outfits → Try-on → Checkout → Rate → Trust. Fix what breaks and tell Charlie about backend errors. Outfits can take up to 30 s while Gemini is the fallback, so Build needs a loading state that long. |
| By 8:30 | **Update the app name** | "As If" is still the working name. Pick the final one with Charlie, since the domain and landing page depend on it. Then change it where users see it: `app.json` (`name`, and the photo-library and Face ID permission texts), the welcome screen's title (`welcome.tsx`), the "You shared only some of your photos" line (`photos.tsx`), `README.md` and PLAN.md's first line. If the name stays "As If", there's nothing to change but `app.json`'s `name` ("LaHacksAI" today). Leave internal ids like the `asif.onboarded` storage key alone: changing them resets everyone's onboarding. |
| 9:30–10:15 | **Create the landing page** | For the MLH Best Domain Name (GoDaddy Registry) prize. Register the domain as soon as the name is final, not at 9:30: pointing it at a host can take a while to take effect. Check MLH's doc (linked in [LA_HACKS.md](LA_HACKS.md)) for which domain endings count and whether there's a free code. One static page: the pitch, the demo video (embed it once recorded), a QR code that opens the app, and the privacy policy (the trust screen's text). Free static hosting (GitHub Pages or Netlify) with the domain pointed at it. |
| 10:15–11:00 | **Demo video and polish** | Record the 2–3 minute video (it should show the eval table, the A/B result and the mandate refusal; Charlie will have the numbers by about 9:30), then add it to the landing page. Polish against Paper. |
| 11:00–11:30 | **Devpost, your half** | The app, trust and checkout sections, plus publishing the landing page. Charlie writes the training story and eval table. |

Decisions since Update 3:

- **No face-matching consent screen.** Dropped. "Pick photos" is the option for people who don't want the scan, and the trust screen and privacy policy say what the scan computes.
- **Stripe Issuing stays,** fallback first (above).
- **`/rate` is built** (`backend/routes/rate.py`, pushed). It serves pairs from `backend/data/rate_pairs.jsonl`, which Charlie builds from two models' eval answers around 9:30. Until then, `GET /rate/next` answers 503 "There are no outfits to compare yet", which the Rate screen shows as is. No app changes needed.
- **Two fixes in your files, both pushed:** the photos screen shows "No outfit photos found…" instead of "Next: your style" when a scan finds none, and `session.tsx` now suggests an anchor once per profile (so Build is prefilled right after onboarding; clearing it sticks) and loads the catalog even when `GET /profile` answers 404 for a new user. Before that fix, new users had an empty catalog until they restarted the app.
- **`comfy` is now formality 1–2** (was 1). Only the reward and retrieval changed; nothing in the app.
