# POST /profile: Gemini reads the user's outfit photos into a StyleProfile and closet (PLAN.md section 4).
# GET /profile and PUT /profile: read and replace the saved profile.
#
# Gemini chooses only from training/vocab.py, and every value is checked here anyway: list values
# outside the vocab are dropped, and a closet item without a valid slot, pattern, formality, color,
# style tag or season is dropped whole. Photos are used for this one call and never stored.

import io
import json

from fastapi import APIRouter, Depends, HTTPException

from backend.schemas import ProfileRequest, StyleProfile
from backend.services import gemini, supabase
from backend.services.images import decode
from training.vocab import COLORS, FIT_SLOTS, FITS, MAX_STYLE_TAGS, PATTERNS, SEASONS, SLOTS, STYLE_TAGS

router = APIRouter()

MAX_PHOTOS = 30
PHOTO_PX = 512  # the app's scan thumbnails are 512 wide already
# Matches the synthetic training profiles (training/gen_profiles.py), so live prompts look the same.
MAX_COLORS = 4
MAX_FITS = 2

PROMPT = f"""You are a stylist reading someone's outfit photos to learn their style. The photos are
numbered from 1 in the order given. Return JSON with:
- summary: one sentence describing their style, as if to them ("Mostly neutrals with relaxed fits...").
- style_tags: 1 to {MAX_STYLE_TAGS} from {list(STYLE_TAGS)}, most typical first.
- colors: the 3 or 4 colors they wear most, from {list(COLORS)}. Map shades to the nearest name
  (grey -> gray, ivory -> cream, camel -> tan, maroon -> burgundy, indigo jeans -> denim).
- fits: 1 or 2 fits they wear most, from {list(FITS)}.
- departments: which clothing sections they shop, from ["men", "women"].
- looks: 1 to 4 named groups of similar outfits, each {{"name": "Weekend errands", "photos": [1, 3]}}.
- closet: each distinct garment you can see them wearing, at most one entry per garment even if
  it appears in several photos: {{"photo": <the photo number it's clearest in>,
  "description": "navy oxford shirt", "slot": one of {list(SLOTS)},
  "colors": 1 to 3 from the colors above, "formality": 1 to 5 (1 athletic or lounge, 2 casual,
  3 smart casual, 4 dressy, 5 formal), "style_tags": 1 to {MAX_STYLE_TAGS} from the style tags above,
  "pattern": one of {list(PATTERNS)}, "fit": one of {list(FITS)} for {sorted(FIT_SLOTS)}, else null,
  "season": 1 to 4 from {list(SEASONS)}}}.
Use only the listed values. Leave out anything you can't see clearly."""


@router.post("/profile")
async def create_profile(req: ProfileRequest, user_id: str = Depends(supabase.current_user)) -> StyleProfile:
    if not req.photos:
        raise HTTPException(422, "Send at least one photo")
    if len(req.photos) > MAX_PHOTOS:
        raise HTTPException(422, f"Send at most {MAX_PHOTOS} photos")
    jpegs = []
    for photo in req.photos:
        try:
            img = decode(photo.base64)
        except Exception:
            raise HTTPException(422, f"Couldn't read photo {photo.id}")
        img.thumbnail((PHOTO_PX, PHOTO_PX))
        buf = io.BytesIO()
        img.save(buf, "JPEG", quality=85)
        jpegs.append(buf.getvalue())

    try:
        text = await gemini.describe_photos(PROMPT, jpegs)
    except Exception:
        raise HTTPException(503, "Couldn't read your photos right now. Try again in a minute.")
    if text is None:
        raise HTTPException(500, "Profiles aren't configured: set GEMINI_API_KEY in backend/.env")
    try:
        answer = json.loads(text)
    except json.JSONDecodeError:
        raise HTTPException(502, "Gemini's answer wasn't JSON. Try again.")
    profile = build_profile(answer if isinstance(answer, dict) else {}, [p.id for p in req.photos])
    await supabase.save_profile(user_id, profile.model_dump())
    return profile


@router.get("/profile")
async def get_profile(user_id: str = Depends(supabase.current_user)) -> StyleProfile:
    profile = await supabase.get_profile(user_id)
    if profile is None:
        raise HTTPException(404, "Make a style profile first")
    return StyleProfile(**profile)


@router.put("/profile")
async def put_profile(profile: StyleProfile, user_id: str = Depends(supabase.current_user)) -> StyleProfile:
    return StyleProfile(**await supabase.save_profile(user_id, profile.model_dump()))


def _pick(values, allowed, limit=None) -> list:
    """The values that are in `allowed`, deduplicated, in order, at most `limit` of them."""
    if not isinstance(values, list):
        return []
    kept = list(dict.fromkeys(v for v in values if isinstance(v, str) and v in allowed))
    return kept[:limit]


def _dicts(values) -> list[dict]:
    return [v for v in values if isinstance(v, dict)] if isinstance(values, list) else []


def _photo_id(number, photo_ids: list[str]):
    """The asset id for Gemini's 1-based photo number, or None if it isn't one of the photos."""
    if isinstance(number, int) and not isinstance(number, bool) and 1 <= number <= len(photo_ids):
        return photo_ids[number - 1]
    return None


def build_profile(answer: dict, photo_ids: list[str]) -> StyleProfile:
    """A StyleProfile from Gemini's answer, keeping only vocab values and real photos."""
    looks = []
    for look in _dicts(answer.get("looks")):
        numbers = look.get("photos") if isinstance(look.get("photos"), list) else []
        ids = list(dict.fromkeys(filter(None, (_photo_id(n, photo_ids) for n in numbers))))
        if isinstance(look.get("name"), str) and look["name"].strip() and ids:
            looks.append({"name": look["name"].strip(), "photo_ids": ids})

    closet = []
    for item in _dicts(answer.get("closet")):
        slot, pattern, formality = item.get("slot"), item.get("pattern"), item.get("formality")
        if slot not in SLOTS or pattern not in PATTERNS or type(formality) is not int or not 1 <= formality <= 5:
            continue
        if slot not in FIT_SLOTS:
            fit = None
        else:  # the catalog tagger's default when the fit isn't clear
            fit = item["fit"] if item.get("fit") in FITS else "regular"
        cleaned = {
            "id": f"closet_{len(closet) + 1}",
            "description": str(item.get("description") or "").strip(),
            "slot": slot,
            "colors": _pick(item.get("colors"), COLORS, 3),
            "formality": formality,
            "style_tags": _pick(item.get("style_tags"), STYLE_TAGS, MAX_STYLE_TAGS),
            "pattern": pattern,
            "fit": fit,
            "season": sorted(_pick(item.get("season"), SEASONS), key=SEASONS.index),
            "photo_id": _photo_id(item.get("photo"), photo_ids),
        }
        if all(cleaned[k] for k in ("description", "colors", "style_tags", "season", "photo_id")):
            closet.append(cleaned)

    return StyleProfile(
        summary=str(answer.get("summary") or "").strip(),
        style_tags=_pick(answer.get("style_tags"), STYLE_TAGS, MAX_STYLE_TAGS),
        colors=_pick(answer.get("colors"), COLORS, MAX_COLORS),
        fits=_pick(answer.get("fits"), FITS, MAX_FITS),
        avoid=[],  # only the user picks what to leave out ("Your style" screen)
        departments=_pick(answer.get("departments"), ("men", "women")),
        looks=looks,
        closet=closet,
    )
