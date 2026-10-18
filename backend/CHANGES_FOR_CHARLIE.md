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

# Change request: two gaps found while designing the rest of the demo path

From Jasmine (app and design). Written 2026-10-17. These came out of the Paper designs for Pick item, Outfits, Try-on, Checkout, Receipt and How did it fit?. Everything else on those screens already fits the current contract.

## 1. "Make it nicer" has no way to ask for it (needed for the demo)

PLAN.md section 8 and the demo script: you say "make it nicer", the agent proposes a $90 upgrade that pushes the cart past the $200 limit, and checkout refuses it. Right now nothing in `OutfitsRequest` asks for an upgrade, and the guard drops any outfit over `budget`, so the app can't get an over-limit cart from `/outfits`.

Options, pick whichever is easiest for you:

- **A (preferred):** add an optional field to `OutfitsRequest`, such as `upgrade_of: str | None = None` (an outfit id). The backend returns one nicer version of that outfit and skips the budget check for it, because the mandate check at `/checkout/cart` is what's supposed to refuse it.
- **B:** a fixed, pre-made "nicer" outfit for the demo anchor, returned by a small endpoint or included in the mocks.

Whatever you choose, tell Jasmine the shape so `src/api/types.ts` matches. Refusing the cart (`/checkout/cart`) is Jasmine's file and already returns `suggestion` for "the closest outfit that fits".

## 2. `ItemFit.liked` (only if "How did it fit?" ships; it's stretch item 2)

The fit screen asks only Too small / Just right / Too big per piece, which is all PLAN.md describes. `ItemFit.liked: bool` is required, so the app would have to send a value the user never gave. Please make it optional in `backend/schemas.py` (`liked: bool | None = None`) and ignore it when it's missing. Jasmine will mirror it in `types.ts`.
