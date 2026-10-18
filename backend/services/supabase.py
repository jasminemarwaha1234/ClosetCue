# Supabase: who the caller is, and the profiles, feedback, preferences and mandates tables.
# PLAN.md section 4 has the design, and backend/supabase_schema.sql creates the tables.
#
# The phone signs in anonymously and sends its access token on every call. Routes take
# `user_id: str = Depends(current_user)` to get the caller's id, or a 401. Everything else
# here runs with the secret key, which bypasses row level security, so every query must be
# filtered by that user_id.
#
# Env (backend/.env): SUPABASE_URL (https://<ref>.supabase.co), SUPABASE_SECRET_KEY (sb_secret_...).

import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import httpx
from dotenv import load_dotenv
from fastapi import Header, HTTPException

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
KEY = os.environ.get("SUPABASE_SECRET_KEY", "")


async def _request(method: str, url: str, **kwargs: Any) -> httpx.Response:
    async with httpx.AsyncClient(timeout=10) as client:
        return await client.request(method, url, **kwargs)


def _check_config() -> None:
    if not URL or not KEY:
        raise HTTPException(500, "Supabase isn't configured: set SUPABASE_URL and SUPABASE_SECRET_KEY in backend/.env")


def _headers(**extra: str) -> dict[str, str]:
    # New secret keys go in the apikey header only; Supabase maps them to service_role.
    return {"apikey": KEY, **extra}


# --- Who is calling ---------------------------------------------------------------

# token -> (user_id, checked_at). Asking Supabase Auth about every request would add a
# round trip to each call, so a token is trusted for a few minutes after it checks out.
_TOKEN_TTL = 300
_tokens: dict[str, tuple[str, float]] = {}


async def user_from_token(token: str) -> Optional[str]:
    """The user id for a Supabase access token, or None if it's invalid or expired."""
    _check_config()
    cached = _tokens.get(token)
    if cached and time.monotonic() - cached[1] < _TOKEN_TTL:
        return cached[0]
    res = await _request("GET", f"{URL}/auth/v1/user", headers=_headers(Authorization=f"Bearer {token}"))
    if res.status_code != 200:
        _tokens.pop(token, None)
        return None
    user_id = res.json()["id"]
    _tokens[token] = (user_id, time.monotonic())
    return user_id


async def current_user(authorization: Optional[str] = Header(None)) -> str:
    """FastAPI dependency: the caller's user id from `Authorization: Bearer <token>`, or 401."""
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(401, "Sign in first: send Authorization: Bearer <Supabase access token>")
    user_id = await user_from_token(authorization[7:].strip())
    if not user_id:
        raise HTTPException(401, "The sign-in has expired or isn't valid. Sign in again.")
    return user_id


# --- Tables -------------------------------------------------------------------------


async def _rest(method: str, table: str, *, params: Optional[dict] = None, json: Any = None, prefer: str = "") -> Any:
    _check_config()
    headers = _headers(**({"Prefer": prefer} if prefer else {}))
    res = await _request(method, f"{URL}/rest/v1/{table}", params=params, json=json, headers=headers)
    if res.status_code >= 400:
        raise HTTPException(502, f"Supabase {table}: {res.status_code} {res.text[:200]}")
    return res.json() if res.content else None


async def get_profile(user_id: str) -> Optional[dict]:
    """The user's StyleProfile as a dict, or None if they haven't made one yet."""
    rows = await _rest("GET", "profiles", params={"user_id": f"eq.{user_id}", "select": "profile"})
    return rows[0]["profile"] if rows else None


async def save_profile(user_id: str, profile: dict) -> dict:
    """Creates or replaces the user's StyleProfile. Returns what was saved."""
    rows = await _rest(
        "POST",
        "profiles",
        params={"on_conflict": "user_id"},
        json={"user_id": user_id, "profile": profile, "updated_at": datetime.now(timezone.utc).isoformat()},
        prefer="resolution=merge-duplicates,return=representation",
    )
    return rows[0]["profile"]


async def rated_pair_ids(user_id: str) -> set[str]:
    """The pair ids the user has already chosen between."""
    rows = await _rest("GET", "feedback", params={"user_id": f"eq.{user_id}", "select": "pair_id"})
    return {row["pair_id"] for row in rows}


async def add_feedback(user_id: str, pair_id: str, choice: str, pair: dict, a_model: str, b_model: str) -> None:
    """Saves an A/B choice. Choosing again for the same pair replaces the earlier answer."""
    await _rest(
        "POST",
        "feedback",
        params={"on_conflict": "user_id,pair_id"},
        json={
            "user_id": user_id,
            "pair_id": pair_id,
            "choice": choice,
            "pair": pair,
            "a_model": a_model,
            "b_model": b_model,
        },
        prefer="resolution=merge-duplicates,return=minimal",
    )


async def add_preference(user_id: str, row: dict) -> None:
    """Saves a "try again with Gemini" pair: prompt, chosen, rejected, rejected_model, request."""
    await _rest("POST", "preferences", json={**row, "user_id": user_id}, prefer="return=minimal")


async def list_preferences() -> list[dict]:
    """Every user's preference rows, oldest first, for training/build_dpo.py."""
    return await _rest("GET", "preferences", params={"select": "*", "order": "id"})


async def create_mandate(user_id: str, mandate: dict) -> dict:
    """Saves a new mandate: id, limit, spent, expires_at (ISO 8601), card_id, card_label."""
    rows = await _rest("POST", "mandates", json={**mandate, "user_id": user_id}, prefer="return=representation")
    return rows[0]


async def get_mandate(user_id: str, mandate_id: str) -> Optional[dict]:
    """The user's mandate with this id, or None. Another user's mandate is None too."""
    rows = await _rest("GET", "mandates", params={"id": f"eq.{mandate_id}", "user_id": f"eq.{user_id}"})
    return rows[0] if rows else None


async def set_mandate_spent(user_id: str, mandate_id: str, spent: float) -> None:
    await _rest(
        "PATCH",
        "mandates",
        params={"id": f"eq.{mandate_id}", "user_id": f"eq.{user_id}"},
        json={"spent": spent},
        prefer="return=minimal",
    )


# --- Delete my data -----------------------------------------------------------------


async def delete_user(user_id: str) -> None:
    """Deletes everything we keep about the user (PLAN.md section 8): their profile,
    feedback, preferences and mandates, then the anonymous account itself. Photos are never stored,
    so there's nothing else. The app signs in again as a new anonymous user afterwards."""
    for table in ("profiles", "feedback", "preferences", "mandates"):
        await _rest("DELETE", table, params={"user_id": f"eq.{user_id}"}, prefer="return=minimal")
    res = await _request("DELETE", f"{URL}/auth/v1/admin/users/{user_id}", headers=_headers())
    if res.status_code not in (200, 204, 404):
        raise HTTPException(502, f"Supabase couldn't delete the account: {res.status_code} {res.text[:200]}")
    for token in [t for t, v in _tokens.items() if v[0] == user_id]:
        del _tokens[token]
