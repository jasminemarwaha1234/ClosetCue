> **Status, Oct 18 (Charlie):** all three are in the contract and PLAN.md.
> - `StyleProfile.formality` is removed from `schemas.py` and `types.ts`.
> - "Make it nicer" is option A, with item ids rather than an outfit id, because the backend doesn't store outfits: `OutfitsRequest.upgrade_of?: string[] | null` holds the current outfit's item and owned ids. `POST /outfits` then returns one outfit with the budget range moved up to (that outfit's total, total + $150], so it can go past `budget_max`. `makeItNicer(req, outfit)` in `client.ts` calls it when mocks are off.
> - The scraper will fill `url` with each product's page (PLAN.md section 5).
> - `/fit`, its types and the fit placeholder screen are gone.
>
> Still open on my side: the final list of allowed color names and `style_tags`.

# Change request: remove "formality" from the style profile

From Jasmine (app and design). Written 2026-10-17.

## Why

On the "Your style" screen, the "How dressed up" 1-5 scale was cut from the design. The app will not show or edit a profile-level formality number. This is a small contract change, so it needs to land in both `backend/schemas.py` and `src/api/types.ts` (they must mirror each other).

## What changes

Only `StyleProfile.formality` goes away. Everything else about formality stays.

### 1. `backend/schemas.py`

In `class StyleProfile`, delete this line:

```python
    formality: int  # 1-5, what they usually wear
```

Result:

```python
class StyleProfile(BaseModel):
    summary: str
    style_tags: list[str]  # same vocabulary as CatalogItem.style_tags
    colors: list[str]  # colors the user wears most
    avoid: list[str]  # style tags or colors to leave out, such as "logos"
    looks: list[Look]
```

### 2. `src/api/types.ts` (Jasmine can do this one)

In `export type StyleProfile`, delete:

```ts
  formality: number; // 1-5, what they usually wear
```

### 3. Things that stay exactly as they are

- `CatalogItem.formality` (1 athleisure ... 5 formal). The reward still checks that items are within 1 level of each other and of the occasion.
- `Occasion` (`everyday`, `work`, `date`, `party`, `formal`, `active`). The occasion is what sets the target formality now.
- The reward function's "Formality coherent" check.

### 4. Anything not written yet that would have used it

- `training/gen_profiles.py`: do not generate a `formality` field for synthetic profiles.
- The `/profile` route's Gemini tagging prompt: do not ask for an overall formality number.
- The `/outfits` prompt format (the style profile is part of the model input): leave out `formality` so the training prompts and the live prompts match. If prompts were already generated with it, regenerate them rather than mixing two formats in one file.
- `POST /fit`: if it updated `profile.formality` from fit feedback, drop that part.

If it is easier to keep the field while the data pipeline is in flight, make it optional instead (`formality: Optional[int] = None`), and the app will ignore it. Removing it fully is cleaner.

## What the "Your style" screen needs from `/profile`

For reference, these are the only fields the screen reads:

| Field | How it shows up |
| --- | --- |
| `summary` | Large editable sentence at the top |
| `style_tags` | Chips under "Style tags" |
| `colors` | Swatches. Please keep these to plain color names ("cream", "black", "olive", "navy") from a small fixed list, because the app maps each name to a hex color. |
| `avoid` | "Leave out" chips the user can remove or add to (the stylist never picks these) |
| `looks` | Named photo groups (`name` plus `photo_ids`) |

Please tell Jasmine the final list of allowed color names and `style_tags`, so the app's swatches and the catalog vocabulary stay in sync.
---

# Change request: "make it nicer" for the checkout demo

From Jasmine (app and design). Written 2026-10-17. This came out of the Paper designs for Pick item, Outfits, Try-on, Checkout and Receipt. Everything else on those screens already fits the current contract.

## "Make it nicer" has no way to ask for it (needed for the demo)

PLAN.md section 8 and the demo script: you say "make it nicer", the agent proposes a $90 upgrade that pushes the cart past the $200 limit, and checkout refuses it. Right now nothing in `OutfitsRequest` asks for an upgrade, and the guard drops any outfit over `budget_max`, so the app can't get an over-limit cart from `/outfits`.

Options, pick whichever is easiest for you:

- **A (preferred):** add an optional field to `OutfitsRequest`, such as `upgrade_of: str | None = None` (an outfit id). The backend returns one nicer version of that outfit and skips the budget check for it, because the mandate check at `/checkout/cart` is what's supposed to refuse it.
- **B:** a fixed, pre-made "nicer" outfit for the demo anchor, returned by a small endpoint or included in the mocks.

Whatever you choose, tell Jasmine the shape so `src/api/types.ts` matches. Refusing the cart (`/checkout/cart`) is Jasmine's file and already returns `suggestion` for "the closest outfit that fits".

For reference, the refused screen also lets the person raise their own limit and pay. That uses the existing `POST /checkout/mandate` with the new limit, then `/checkout/confirm` after Face ID, so it needs nothing from you. The agent still can never go over a limit; only the person can raise it.

## Dropped: "How did it fit?"

We can't know when an order arrives, so the fit screen is cut from the app. Nothing from the app will call `POST /fit`.

---

# Change request: real product URLs for "View at retailer"

From Jasmine (app and design). Written 2026-10-17, after the PLAN.md section 8 update.

The outfit cards and the receipt now have a **View at retailer** link on every item, opened in an in-app browser. The app reads `CatalogItem.url` and hides the link when it's empty. Nothing in the contract changes; this is about filling the field.

1. **Scraper (section 5):** set `url` to the item's real product page, for example `https://<store>/products/<handle>` from the store's `products.json`. Please don't leave it empty or point it at the store's home page.
2. **`/catalog`, `/outfits` and `/checkout/confirm`:** return the full `CatalogItem` with `url` for each item, including `Outfit.swaps` and `Receipt.items`. The receipt is where the demo shows that no order was placed, and that the links go to the real pages.
3. **Training prompts:** no change. `url` doesn't need to go into the model's input.

The receipt's "Demo: no order was placed and no money moved." line is entirely in the app, so it needs nothing from you.
