> **Status, Oct 18 (Charlie):** all three are in the contract and PLAN.md.
> - `StyleProfile.formality` is removed from `schemas.py` and `types.ts`.
> - "Make it nicer" is option A, with item ids rather than an outfit id, because the backend doesn't store outfits: `OutfitsRequest.upgrade_of?: string[] | null` holds the current outfit's item and owned ids. `POST /outfits` then returns one outfit with the budget range moved up to (that outfit's total, total + $150], so it can go past `budget_max`. `makeItNicer(req, outfit)` in `client.ts` calls it when mocks are off.
> - The scraper will fill `url` with each product's page (PLAN.md section 5).
> - `/fit`, its types and the fit placeholder screen are gone.
>
> - The color names and `style_tags` were reworked after this note. The final lists, with the 8 occasions and the new `pattern`, `fit` and `fits` fields, are in [JANGES_FOR_JASMINE.md](JANGES_FOR_JASMINE.md) ("Update 2, Sunday Oct 18"), `training/vocab.py` and PLAN.md section 5.
>
> `swatches` in `src/theme/index.ts` now covers all 25 colors, with your `gold` and `silver` values.

> **Status, Oct 18 morning (Jasmine):** thanks, everything above is merged into my branch with no conflicts. `gold` and `silver` are in `swatches` now, and `GeneratedBy`'s spelling is fine as it is. What's open for you:
> 1. **Supabase: I did it, so you don't have to** (section at the bottom). Your `/profile` and `/rate` routes just call the helpers in `backend/services/supabase.py`.
> 2. **Keep `image` in `catalog.json`** when you tag it: `/tryon` sends each item's product photo to Gemini. Also make `price` a number (it's the string `"185.0"` in `catalog_raw.json`).
> 3. **Share the Gemini key** with me privately: `/tryon` is mine and uses Gemini image editing (your NEXT_STEPS item 8).

> **What changed since your last push ("Add a handoff of the model and backend next steps", Oct 18 01:30), Jasmine:**
>
> **Run after pulling:** `pip install -r backend/requirements.txt` (new: `httpx`, `python-dotenv`, `google-genai`) and `npm install` (new: `@supabase/supabase-js`, `expo-sqlite`).
>
> **The contract didn't change:** `backend/schemas.py` and `src/api/types.ts` are untouched.
>
> | File | Change |
> | --- | --- |
> | `backend/main.py` (shared) | Two `include_router` lines: `me` and `tryon` |
> | `backend/requirements.txt` (shared) | Added `httpx`, `python-dotenv`, `google-genai` |
> | `backend/services/supabase.py` (new, your area) | Supabase: `current_user` token check, profile/feedback/mandate helpers, `delete_user`. See "Supabase: done by Jasmine" below |
> | `backend/supabase_schema.sql` (new) | The `profiles`, `feedback`, `mandates` tables with RLS. Jasmine runs it once in the dashboard |
> | `backend/routes/me.py` (new) | `DELETE /me` |
> | `backend/routes/tryon.py`, `backend/services/tryon.py` (new) | `POST /tryon` with Gemini image editing |
> | `src/api/mocks.ts` | Mock catalog is 18 real items from `catalog_raw.json` (same ids); mock outfits follow the anchor, budget and max per item |
> | `src/api/client.ts` | Sends the Supabase token; `tryOn` always calls the backend; `deleteMe()`. Your `makeItNicer` is unchanged |
> | `src/lib/supabase.ts` (new), `src/lib/session.tsx` | Anonymous sign-in on launch |
> | `src/lib/confirm.ts` | Pay asks with an in-app dialog in Expo Go, Face ID in a dev build |
> | `src/app/outfits.tsx`, `src/components/ui.tsx` | × to leave a piece out, Swap pill, product photos |
> | `src/app/(tabs)/build.tsx`, `src/components/RangeSlider.tsx` | Budget slider from $10 with uneven steps |
> | `src/app/onboarding/photos.tsx`, `src/app/_layout.tsx` | Onboarding can't be swiped back to |
> | `src/theme/index.ts` | `gold` and `silver` swatches |
> | `package.json`, `package-lock.json`, `app.json` | `@supabase/supabase-js`, `expo-sqlite` and its config plugin |
>
> **Env:** `backend/.env` now needs `SUPABASE_URL` and `SUPABASE_SECRET_KEY`, which I'll send you privately. `GEMINI_API_KEY` needs billing on its Google project for try-on (image models have no free tier). Text tagging works without it.

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

---

# Accounts and the payment picker (FYI, nothing to do)

From Jasmine, 2026-10-18. App-only; no backend or contract changes. Merged your vocab/occasion push into my branch with no conflicts.

- **Sign-in:** the welcome screen has a username and password (Supabase email/password, with each username mapped to `<username>@users.asif.app` and "Confirm email" off) and Continue as guest (anonymous). Google is postponed. A guest can save an account later from Your style (`updateUser`) and keeps the same user id, so your `profiles` row stays attached. The app no longer signs in silently on launch; `index.tsx` opens Build when the account already finished onboarding.
- **Payment picker:** checkout's "Pay with" sheet (Apple Pay, Visa, PayPal) is simulated and labeled as a demo. The mandate check, refusal and agent card are unchanged.
- **Files:** `src/lib/supabase.ts`, `src/lib/onboarding.ts` (new), `src/lib/payment.ts` (new), `src/lib/session.tsx`, `src/app/index.tsx`, `src/app/onboarding/welcome.tsx`, `src/app/onboarding/photos.tsx`, `src/app/_layout.tsx` (welcome header hidden), `src/app/(tabs)/style.tsx` (account card), `src/app/checkout/index.tsx`, `src/app/checkout/receipt.tsx`, `src/components/AccountCard.tsx`, `src/components/AccountFields.tsx`, `src/components/PaySheet.tsx`, `src/components/logos.tsx` (all new), `src/api/client.ts` (`usingMocks`), `src/theme/index.ts` (`brands`, `scrim`), `package.json` (`react-native-svg`).

- **Your style uses the real profile now** (`src/app/(tabs)/style.tsx`): summary, style tags, colors, fits, Leave out (`avoid`), closet and looks all come from `StyleProfile`. Editing the summary, Leave out or the new **Fits you wear** chips saves with `PUT /profile`, so your route gets the whole profile back each time.

---

# The app is called ClosetCue now (FYI)

From Jasmine, 2026-10-18. Renamed from As If in `app.json` (app name, slug `closetcue`, photo and Face ID prompts), the welcome screen, README's title, PLAN.md's first line and the Paper frames ("ClosetCue / …"). Unchanged on purpose: the `lahacksai://` link scheme, the `~/.venvs/as-if` folder, and the internal account domain `users.asif.app`, since changing those would break existing sign-ins and setup. If any Devpost or demo text says As If, it should say ClosetCue.
