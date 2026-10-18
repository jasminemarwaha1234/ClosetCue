"""Tag training/catalog_raw.json with Gemini into training/catalog.json.

Run from the repo root: python -m training.tag_catalog [--limit N]

Gemini fills department, colors, formality, style_tags, season, pattern and fit from each item's text and
image, choosing only from training/vocab.py. Every answer is checked against the vocab in
Python; bad or missing items are retried one at a time, then dropped. Results are cached per
item id in training/.tag_cache.json, so a rerun only tags what's left. Cached entries that no
longer pass the vocab checks are tagged again.

The key is GEMINI_API_KEY in backend/.env. The free tier allows 5 requests a minute and 20 a
day per model, so calls go one at a time, at least DELAY seconds apart, and move to the next of
MODELS when one runs out for the day. Each cached item records the model that tagged it.
"""

import argparse
import io
import json
import re
import time
import urllib.request
from collections import Counter
from pathlib import Path
from typing import Literal

from google import genai
from google.genai import errors, types
from PIL import Image
from pydantic import BaseModel

from training.vocab import (
    COLORS, DEPARTMENTS, FIT_SLOTS, FITS, MAX_STYLE_TAGS, PATTERNS, SEASONS, SLOTS, STYLE_TAGS,
)

HERE = Path(__file__).parent
ROOT = HERE.parent
CACHE = HERE / ".tag_cache.json"
MODELS = ["gemini-3.8-flash", "gemini-3.7-flash", "gemini-3.6-flash", "gemini-3.5-flash",
          "gemini-3-flash-preview"]
BATCH = 15
TRIES = 3
IMAGE_PX = 384
DELAY = 13

PROMPT = f"""You tag clothing items for an outfit recommender. For each item below, look at the
image and read its text, then give the tags below. The photo often shows a model in a full
outfit: tag only the garment the item names (its slot says which), ignoring everything else.
- department: who it's sold for, one of {list(DEPARTMENTS)}. If a department hint is given, use it.
- colors: 1 to 3 main colors of that item, most dominant first; a solid item gets one. Choose
  from {list(COLORS)}. Map shades to the nearest name: grey -> gray,
  ivory/ecru/off-white -> cream, sage/mint/muted green -> muted-green, deep/emerald/hunter
  green -> forest-green, light blue/sky -> light-blue, indigo jeans -> denim,
  maroon/wine -> burgundy, lavender -> lilac, camel -> tan. Use "denim" only for denim fabric.
  Use "gold"/"silver" only for metal (jewelry, hardware-heavy items). When the name or url
  handle names a color, that's the item's main color (the photo can make it look different).
- formality: 1 to 5. 1 = athletic or loungewear (leggings, sports bras, sweatpants, slides);
  2 = casual (tees, hoodies, jeans, sneakers, caps, shorts); 3 = smart casual (polos, chinos,
  knit sweaters, loafers, casual dresses, leather boots); 4 = dressy (button-ups, dress shirts,
  blazers, tailored trousers, silk blouses, cocktail dresses, heels, dress shoes); 5 = formal
  (suits, tuxedos, tuxedo shirts, gowns). Most items are 2 or 3.
- style_tags: 1 to {MAX_STYLE_TAGS} from {list(STYLE_TAGS)}.
- pattern: one of {list(PATTERNS)}. stripe = any stripes; check = plaid, gingham or
  houndstooth; small-print = small repeating prints like florals or dots that read as texture
  from a distance; large-print = bold, large-scale prints; graphic = printed graphics, artwork,
  or a logo or wordmark as a visible design feature.
- fit: for {sorted(FIT_SLOTS)}, one of {list(FITS)}, read from the name or description
  ("relaxed fit" -> relaxed, "slim" -> slim, "boxy" or "oversized" -> oversized); regular
  when unstated. null for shoes and accessories.
- season: the seasons it suits, 1 to 4 from {list(SEASONS)}. Year-round basics get all four.

Return one entry per item, using the item's id exactly."""


class Tags(BaseModel):
    id: str
    department: Literal[DEPARTMENTS]
    colors: list[Literal[COLORS]]
    formality: int
    style_tags: list[Literal[STYLE_TAGS]]
    season: list[Literal[SEASONS]]
    pattern: Literal[PATTERNS]
    fit: Literal[FITS] | None


def api_key():
    env = (ROOT / "backend" / ".env").read_text()
    return re.search(r"^GEMINI_API_KEY=(.*)$", env, re.M).group(1).strip().strip("\"'")


def image_part(url):
    try:
        req = urllib.request.Request(f"{url}?width={IMAGE_PX * 2}", headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            img = Image.open(io.BytesIO(resp.read())).convert("RGB")
    except Exception as e:
        print(f"  image failed ({e}), tagging from text only: {url}")
        return None
    img.thumbnail((IMAGE_PX, IMAGE_PX))
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=85)
    return types.Part.from_bytes(data=buf.getvalue(), mime_type="image/jpeg")


def item_text(item):
    fields = {k: item[k] for k in ("id", "name", "brand", "slot", "product_type", "tags", "description")}
    fields["url handle"] = item["url"].rsplit("/", 1)[1]
    if item["department_hint"]:
        fields["department hint"] = item["department_hint"]
    return json.dumps(fields, ensure_ascii=False)


def validate(item, tags):
    """Return the cleaned tags for one item, or raise ValueError saying what's wrong."""
    colors = list(dict.fromkeys(tags.get("colors") or []))
    style_tags = list(dict.fromkeys(tags.get("style_tags") or []))
    season = [s for s in SEASONS if s in (tags.get("season") or [])]
    department = item["department_hint"] or tags.get("department")
    if department not in DEPARTMENTS:
        raise ValueError(f"department {department!r}")
    if not 1 <= len(colors) <= 3 or not set(colors) <= set(COLORS):
        raise ValueError(f"colors {colors}")
    if tags.get("formality") not in (1, 2, 3, 4, 5):
        raise ValueError(f"formality {tags.get('formality')!r}")
    if not 1 <= len(style_tags) <= MAX_STYLE_TAGS or not set(style_tags) <= set(STYLE_TAGS):
        raise ValueError(f"style_tags {style_tags}")
    if not season:
        raise ValueError("no season")
    if tags.get("pattern") not in PATTERNS:
        raise ValueError(f"pattern {tags.get('pattern')!r}")
    fit = tags.get("fit")
    if fit not in (FITS if item["slot"] in FIT_SLOTS else (None,)):
        raise ValueError(f"fit {fit!r} for a {item['slot']}")
    return {"department": department, "colors": colors, "formality": tags["formality"],
            "style_tags": style_tags, "season": season, "pattern": tags["pattern"], "fit": fit}


def generate(client, contents, state):
    backoff = 30
    while True:
        wait = state["last"] + DELAY - time.time()
        if wait > 0:
            time.sleep(wait)
        state["last"] = time.time()
        try:
            resp = client.models.generate_content(
                model=MODELS[state["model"]],
                contents=contents,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json", response_schema=list[Tags], temperature=0,
                ),
            )
            return json.loads(resp.text)
        except errors.APIError as e:
            if e.code == 429 and "PerDay" in str(e):
                state["model"] += 1
                if state["model"] == len(MODELS):
                    raise SystemExit("Every model is out of daily quota. Rerun tomorrow to finish.")
                print(f"  daily quota used up, switching to {MODELS[state['model']]}")
                continue
            if e.code not in (429, 500, 502, 503, 504) or backoff > 320:
                raise
            print(f"  {e.code} from Gemini, waiting {backoff} s")
            time.sleep(backoff)
            backoff *= 2


def tag_batch(client, items, stats, state):
    """Tag items in one call. Return {id: tags} for valid answers and {id: reason} for the rest."""
    contents = [PROMPT]
    for item in items:
        contents.append(item_text(item))
        part = image_part(item["image"])
        if part:
            contents.append(part)
    stats["calls"] += 1
    try:
        answers = {a.get("id"): a for a in generate(client, contents, state)}
    except (errors.APIError, json.JSONDecodeError) as e:
        return {}, {item["id"]: f"call failed: {e}" for item in items}
    good, bad = {}, {}
    for item in items:
        if item["id"] not in answers:
            bad[item["id"]] = "missing from the answer"
            continue
        try:
            good[item["id"]] = {**validate(item, answers[item["id"]]), "model": MODELS[state["model"]]}
        except ValueError as e:
            bad[item["id"]] = str(e)
    return good, bad


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, help="tag only the first N items")
    args = parser.parse_args()

    all_raw = json.loads((HERE / "catalog_raw.json").read_text())
    raw = all_raw[: args.limit]
    by_id = {item["id"]: item for item in all_raw}
    cache = {}
    for item_id, tags in (json.loads(CACHE.read_text()) if CACHE.exists() else {}).items():
        try:
            cache[item_id] = {**validate(by_id[item_id], tags), "model": tags["model"]}
        except (KeyError, ValueError):
            pass
    client = genai.Client(api_key=api_key(), http_options=types.HttpOptions(
        timeout=120_000, retry_options=types.HttpRetryOptions(attempts=1)))
    todo = [item for item in raw if item["id"] not in cache]
    print(f"{len(raw) - len(todo)} cached, {len(todo)} to tag")

    stats = Counter()
    state = {"last": 0.0, "model": 0}
    dropped = {}
    start = time.time()
    for i in range(0, len(todo), BATCH):
        good, bad = tag_batch(client, todo[i : i + BATCH], stats, state)
        for item_id, reason in bad.items():
            for _ in range(TRIES - 1):
                print(f"  retrying {item_id} alone: {reason}")
                retry_good, retry_bad = tag_batch(client, [by_id[item_id]], stats, state)
                good.update(retry_good)
                if item_id in good:
                    break
                reason = retry_bad[item_id]
            else:
                dropped[item_id] = reason
        cache.update(good)
        CACHE.write_text(json.dumps(cache, indent=1))
        print(f"{min(i + BATCH, len(todo))}/{len(todo)} tagged, {stats['calls']} calls, {time.time() - start:.0f} s")

    rows = []
    for item in raw:
        if item["id"] in cache:
            tags = cache[item["id"]]
            rows.append({
                "id": item["id"], "name": item["name"], "brand": item["brand"], "slot": item["slot"],
                "department": tags["department"], "price": item["price"], "colors": tags["colors"],
                "formality": tags["formality"], "style_tags": tags["style_tags"], "season": tags["season"],
                "pattern": tags["pattern"], "fit": tags["fit"],
                "image": item["image"], "url": item["url"],
            })
    try:
        from backend.schemas import CatalogItem
        for row in rows:
            CatalogItem(**row)
    except ImportError:
        print("backend.schemas not importable, skipped schema check")
    (HERE / "catalog.json").write_text(json.dumps(rows, indent=2, ensure_ascii=False) + "\n")

    print(f"\nWrote {len(rows)} items to training/catalog.json ({stats['calls']} calls this run)")
    for item_id, reason in dropped.items():
        print(f"  dropped {item_id} ({by_id[item_id]['name']}): {reason}")
    print("models:", dict(Counter(cache[r["id"]]["model"] for r in rows)))
    for field in ("department", "formality"):
        print(f"{field}:", dict(sorted(Counter(r[field] for r in rows).items())))
    for field in ("pattern", "fit"):
        print(f"{field}:", dict(Counter(r[field] for r in rows).most_common()))
    for field in ("colors", "style_tags", "season"):
        print(f"{field}:", dict(Counter(v for r in rows for v in r[field]).most_common()))
    print("formality by slot:")
    for slot in SLOTS:
        print(f"  {slot}:", dict(sorted(Counter(r["formality"] for r in rows if r["slot"] == slot).items())))


if __name__ == "__main__":
    main()
