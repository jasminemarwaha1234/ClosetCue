# Gemini calls: the last fallback for /outfits when neither Llama answers well, and tagging the
# photos for POST /profile.
#
# Env (backend/.env): GEMINI_API_KEY. The free tier's daily quota is per model, so a 429 moves on
# to the next of MODELS.

import asyncio
import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from google import genai
from google.genai import errors, types

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

# Same fast models as training/tag_catalog.py, newest first.
MODELS = ["gemini-3.8-flash", "gemini-3.7-flash", "gemini-3.6-flash", "gemini-3.5-flash", "gemini-3-flash-preview"]
TIMEOUT = 60  # seconds
TEMPERATURE = 0.7  # above 0 so a retry can give a different answer


async def chat(messages: list[dict]) -> Optional[str]:
    """Gemini's reply to [system, user] messages, or None when GEMINI_API_KEY isn't set."""
    system, user = messages
    config = types.GenerateContentConfig(
        system_instruction=system["content"], response_mime_type="application/json", temperature=TEMPERATURE,
    )
    return await _generate(user["content"], config)


async def describe_photos(prompt: str, jpegs: list[bytes]) -> Optional[str]:
    """Gemini's JSON answer to a prompt about JPEG photos, or None when GEMINI_API_KEY isn't set."""
    parts = [types.Part.from_text(text=prompt)]
    parts += [types.Part.from_bytes(data=jpeg, mime_type="image/jpeg") for jpeg in jpegs]
    config = types.GenerateContentConfig(response_mime_type="application/json", temperature=0)
    return await _generate(parts, config)


async def _generate(contents, config: types.GenerateContentConfig) -> Optional[str]:
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        return None
    client = genai.Client(api_key=key)
    for model in MODELS:
        try:
            res = await asyncio.wait_for(
                client.aio.models.generate_content(model=model, contents=contents, config=config), TIMEOUT,
            )
            return res.text
        except errors.ClientError as e:
            if e.code != 429 or model == MODELS[-1]:
                raise
