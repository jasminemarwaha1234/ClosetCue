# Try-on: the user's photo wearing an outfit's catalog items, made by Gemini image editing
# (PLAN.md sections 3 and 4). Jasmine's file; the rest of the Gemini work is in gemini.py.
#
# The photo is used for this one call and never stored. Only catalog items are sent:
# pieces the user owns are already in their photo, so the prompt keeps everything else as is.
#
# Env (backend/.env): GEMINI_API_KEY.

import asyncio
import logging
import base64
import io
import json
import os
from functools import cache
from pathlib import Path

import httpx
from dotenv import load_dotenv
from fastapi import HTTPException
from google import genai
from google.genai import errors, types
from PIL import Image

from backend.services.images import decode

load_dotenv(Path(__file__).resolve().parents[1] / ".env")
log = logging.getLogger(__name__)

# Nano Banana 2.1, Gemini's main image-editing model. It takes up to 10 garment images
# alongside the person, which covers a whole outfit.
MODEL = "gemini-nano-banana-2.1"
MAX_ITEMS = 8
TIMEOUT = 90  # seconds; a try-on normally takes 10-20
GARMENT_WIDTH = 768  # Shopify's CDN resizes on request; full-size product photos are slow to send

TRAINING = Path(__file__).resolve().parents[2] / "training"


@cache
def _catalog() -> dict[str, dict]:
    """Catalog items by id: the tagged catalog.json once it exists, else the raw scrape."""
    for name in ("catalog.json", "catalog_raw.json"):
        path = TRAINING / name
        if path.exists():
            return {item["id"]: item for item in json.loads(path.read_text())}
    return {}


@cache
def _client() -> genai.Client:
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        raise HTTPException(500, "Try-on isn't configured: set GEMINI_API_KEY in backend/.env")
    return genai.Client(api_key=key)


def _sized(url: str) -> str:
    if "cdn.shopify.com" not in url:
        return url
    return f"{url}{'&' if '?' in url else '?'}width={GARMENT_WIDTH}"


async def _garment(client: httpx.AsyncClient, item: dict) -> tuple[bytes, str]:
    res = await client.get(_sized(item["image"]), follow_redirects=True)
    if res.status_code != 200:
        raise HTTPException(502, f"Couldn't load the product photo for {item['name']}")
    mime = res.headers.get("content-type", "image/jpeg").split(";")[0]
    return res.content, mime


def _prompt(items: list[dict]) -> str:
    pieces = "\n".join(f"- Image {n + 2}: {item['name']} ({item['slot']})" for n, item in enumerate(items))
    return (
        "Image 1 is a photo of a person. The other images are clothing products:\n"
        f"{pieces}\n\n"
        "Edit image 1 so the person is wearing these products. Each product replaces whatever "
        "they're wearing in the same place (a top replaces their top, shoes replace their shoes). "
        "Match each product's color, pattern, fabric and cut exactly, and fit it naturally to "
        "their body and pose. Keep everything else unchanged: their face, hair, skin, body shape, "
        "pose, any clothes not being replaced, the background and the lighting. "
        "Return one photorealistic image with the same framing as image 1."
    )


def _jpeg(data: bytes) -> str:
    img = Image.open(io.BytesIO(data)).convert("RGB")
    out = io.BytesIO()
    img.save(out, "JPEG", quality=88)
    return base64.b64encode(out.getvalue()).decode()


async def try_on(photo_b64: str, item_ids: list[str]) -> str:
    """The person in `photo_b64` wearing the catalog items, as base64 JPEG."""
    if not item_ids:
        raise HTTPException(422, "Send at least one catalog item to try on")
    if len(item_ids) > MAX_ITEMS:
        raise HTTPException(422, f"Try on at most {MAX_ITEMS} items at a time")
    catalog = _catalog()
    unknown = [i for i in item_ids if i not in catalog]
    if unknown:
        raise HTTPException(422, f"Not in the catalog: {', '.join(unknown)}")
    items = [catalog[i] for i in item_ids]
    if missing := [i["name"] for i in items if not i.get("image")]:
        raise HTTPException(422, f"No product photo for: {', '.join(missing)}")

    try:
        person = decode(photo_b64)
    except Exception:
        raise HTTPException(422, "Couldn't read that photo")
    buf = io.BytesIO()
    person.save(buf, "JPEG", quality=90)

    async with httpx.AsyncClient(timeout=15) as http:
        garments = await asyncio.gather(*(_garment(http, item) for item in items))

    # Re-encoded so phone formats like HEIC and EXIF rotation reach Gemini as an upright JPEG.
    parts = [types.Part.from_text(text=_prompt(items)), types.Part.from_bytes(data=buf.getvalue(), mime_type="image/jpeg")]
    parts += [types.Part.from_bytes(data=data, mime_type=mime) for data, mime in garments]

    try:
        res = await asyncio.wait_for(_client().aio.models.generate_content(model=MODEL, contents=parts), TIMEOUT)
    except asyncio.TimeoutError:
        raise HTTPException(504, "Try-on took too long. Try again, or use the flat lay.")
    except errors.ClientError as e:
        if e.code == 429:
            # The free tier has no image generation: the key's Google project needs billing on.
            raise HTTPException(503, "Try-on is out of Gemini quota. The flat lay still works.")
        raise HTTPException(502, f"Gemini couldn't make the try-on: {e.message}")
    except errors.APIError as e:
        raise HTTPException(502, f"Gemini couldn't make the try-on: {e.message}")

    candidates = res.candidates or []
    # A candidate can come back with no content or no parts, e.g. when Gemini declines the photo.
    parts = [p for c in candidates for p in ((c.content.parts if c.content else None) or [])]
    images = [p.inline_data.data for p in parts if p.inline_data and p.inline_data.data]
    if not images:
        reasons = {str(c.finish_reason).split(".")[-1] for c in candidates if c.finish_reason}
        blocked = res.prompt_feedback.block_reason if res.prompt_feedback else None
        text = " ".join(p.text for p in parts if p.text).strip()
        log.warning("Try-on returned no image: finish=%s blocked=%s text=%r", reasons, blocked, text[:200])
        # Usually Gemini declining the photo; the app keeps the flat lay.
        raise HTTPException(
            502,
            "Gemini couldn't dress this photo. Try a different one: a full-body photo of just you, "
            "standing, in good light.",
        )
    return _jpeg(images[0])
