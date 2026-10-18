> **Status, Oct 18 (Charlie):** all three are in the contract and PLAN.md.
> - `StyleProfile.formality` is removed from `schemas.py` and `types.ts`.
> - "Make it nicer" is option A, with item ids rather than an outfit id, because the backend doesn't store outfits: `OutfitsRequest.upgrade_of?: string[] | null` holds the current outfit's item and owned ids. `POST /outfits` then returns one outfit with the budget range moved up to (that outfit's total, total + $150], so it can go past `budget_max`. `makeItNicer(req, outfit)` in `client.ts` calls it when mocks are off.
> - The scraper will fill `url` with each product's page (PLAN.md section 5).
> - `/fit`, its types and the fit placeholder screen are gone.
>
> - The color names and `style_tags` are final, in `training/vocab.py` (also listed in PLAN.md section 5, Catalog). Colors: white, cream, beige, tan, khaki, brown, gray, charcoal, black, navy, denim, blue, green, olive, yellow, orange, red, burgundy, pink, lilac, purple, gold, silver. Style tags: minimal, classic, relaxed, tailored, smart-casual, preppy, streetwear, graphic, workwear, outdoors, athleisure, vintage, bohemian, romantic, edgy, trendy, logos.
>
> Nothing is open on my side. One gap on the app side: `swatches` in `src/theme/index.ts` has no `gold` or `silver` (jewelry will use them), so those fall back to `surfaceMuted`.

> **Status, Oct 18 morning (Jasmine):** thanks, everything above is merged into my branch with no conflicts. `gold` and `silver` are in `swatches` now, and `GeneratedBy`'s spelling is fine as it is. What's open for you:
> 1. **Supabase: I did it, so you don't have to** (section at the bottom). Your `/profile` and `/rate` routes just call the helpers in `backend/services/supabase.py`.
> 2. **Keep `image` in `catalog.json`** when you tag it: `/tryon` sends each item's product photo to Gemini. Also make `price` a number (it's the string `"185.0"` in `catalog_raw.json`).
> 3. **Share the Gemini key** with me privately: `/tryon` is mine and uses Gemini image editing (your NEXT_STEPS item 8).

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

---

# Supabase: done by Jasmine (app and backend)

From Jasmine. Written 2026-10-18. PLAN.md gives Supabase to you, but section 10 lets me take it if you're busy, so I built all of it. It's on my branch `jasmine/frontend` until we merge.

**The project exists.** I'll send you the URL and secret key privately for your `backend/.env` (`SUPABASE_URL`, `SUPABASE_SECRET_KEY`). `SUPABASE_URL` is the bare `https://<ref>.supabase.co`, not the `/rest/v1/` one.

**What's built:**

| Piece | Where |
| --- | --- |
| Anonymous sign-in on launch; every backend call sends `Authorization: Bearer <token>` | `src/lib/supabase.ts`, `api()` in `src/api/client.ts` |
| Tables `profiles`, `feedback`, `mandates`, RLS on with no policies (only the backend's secret key can touch them), rows deleted with the user | `backend/supabase_schema.sql` (run once in the SQL editor) |
| Who's calling: `current_user` dependency, 401 without a valid token | `backend/services/supabase.py` |
| Table helpers | same file |
| `DELETE /me` and the app's `deleteMe()` | `backend/routes/me.py`, `src/api/client.ts` |

**How to use it in your routes** (`profile.py`, `feedback.py`):

```python
from fastapi import Depends
from backend.services import supabase

@router.get("/profile")
async def get_profile(user_id: str = Depends(supabase.current_user)) -> StyleProfile:
    profile = await supabase.get_profile(user_id)  # dict or None
    if profile is None:
        raise HTTPException(404, "No profile yet")
    return StyleProfile(**profile)
```

- `get_profile(user_id)` → dict or None; `save_profile(user_id, profile_dict)` creates or replaces it. Use it for `POST` and `PUT /profile`.
- `add_feedback(user_id, pair_id, choice, pair_dict, a_model, b_model)` for `POST /rate`. `a_model`/`b_model` are which model made each side (never sent to the app), so the table exports straight to DPO pairs. Rating the same pair twice keeps the last answer.
- `create_mandate`, `get_mandate`, `set_mandate_spent` are for my checkout.
- Every helper runs with the secret key, which skips row level security, so always pass the `user_id` from `current_user`, never one from the request body.
- It loads `backend/.env` with `python-dotenv` (added to `requirements.txt` with `httpx`). Your Gemini and Veri services can read `os.environ` after importing it, or call `load_dotenv` the same way.

**Shared files I touched:** `backend/main.py` (one `include_router` for `me`) and `backend/requirements.txt` (two lines). `/tryon` will add one more `include_router` line later.

---

# Try-on is built (FYI, nothing to do)

From Jasmine, 2026-10-18.

- `POST /tryon` is in `backend/routes/tryon.py` and `backend/services/tryon.py` (Gemini `gemini-nano-banana-2.1`), registered with one line in `main.py`. `google-genai` is in `requirements.txt`.
- It reads product photos from `training/catalog.json`, or `catalog_raw.json` until that exists, so please keep `image` in the tagged catalog.
- The app's mock catalog is now 18 real items from `catalog_raw.json` with their real ids, images and URLs, so mocks and the real catalog line up.
- **Heads-up for your tagging:** the Gemini key's project is on the free tier, where image models have a quota of 0. Text models still work there, with tight per-minute limits. Try-on needs billing turned on for the key's Google project.
