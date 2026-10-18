# Chat calls to our Llama models served on Veri, through the deployments' OpenAI-compatible API
# (POST <url>/chat/completions). Any OpenAI-compatible server works, so a model can be pointed
# elsewhere for testing.
#
# Env (backend/.env), one set per model, where <MODEL> is OUR_LLAMA (the trained one) or
# BASE_LLAMA (untrained, the fallback):
#   <MODEL>_URL      https://api.veri.studio/v1/deployments/<deployment id>
#   <MODEL>_NAME     the model name the server expects
#   <MODEL>_API_KEY  the Veri key (vk_...)
# A model whose URL is unset is skipped.

import os
from pathlib import Path
from typing import Optional

import httpx
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

TIMEOUT = 60  # seconds; a scaled-to-zero deployment answers 503 while it wakes, which counts as a failure
TEMPERATURE = 0.7  # above 0 so a retry can give a different answer
MAX_TOKENS = 1024


def outfits_schema(ids: list[str], outfits: int) -> dict:
    """vLLM constrained decoding: exactly `outfits` outfits whose items can only be the given ids."""
    outfit = {
        "type": "object", "additionalProperties": False, "required": ["items", "reason"],
        "properties": {
            "items": {"type": "array", "minItems": 2, "maxItems": 6, "items": {"type": "string", "enum": ids}},
            "reason": {"type": "string"},
        },
    }
    return {"type": "json_schema", "json_schema": {"name": "outfits", "strict": True, "schema": {
        "type": "object", "additionalProperties": False, "required": ["outfits"],
        "properties": {"outfits": {"type": "array", "minItems": outfits, "maxItems": outfits, "items": outfit}},
    }}}


async def chat(model: str, messages: list[dict], ids: list[str], outfits: int) -> Optional[str]:
    """The reply of model OUR_LLAMA or BASE_LLAMA, or None when it isn't configured.
    Item ids are constrained to `ids`, so the model can't name an item it wasn't offered."""
    url = os.environ.get(f"{model}_URL", "").rstrip("/")
    if not url:
        return None
    key = os.environ.get(f"{model}_API_KEY", "")
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        res = await client.post(
            f"{url}/chat/completions",
            headers={"Authorization": f"Bearer {key}"},
            json={
                "model": os.environ.get(f"{model}_NAME", ""),
                "messages": messages,
                "temperature": TEMPERATURE,
                "max_tokens": MAX_TOKENS,
                "response_format": outfits_schema(ids, outfits),
            },
        )
    res.raise_for_status()
    return res.json()["choices"][0]["message"]["content"]
