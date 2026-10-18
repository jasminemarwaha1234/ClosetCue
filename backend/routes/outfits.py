# POST /outfits: outfits for the user's profile, occasion, budget and anchor (PLAN.md sections 4 and 5).
#
# Retrieval picks the candidates, a model chooses outfits from them, and the reward's checks
# guard every answer: an outfit is dropped when it fails a gate (bad JSON, an invented item), misses
# the anchor, or is outside the budget. Totals come from catalog prices; the model doesn't state one.
# Each model gets a second try when fewer than MIN_OUTFITS survive, then the next model in CHAIN
# answers. If none reaches MIN_OUTFITS, the best partial answer is returned; a 503 only when no
# outfit survived at all.

import logging
import re
import uuid
from typing import Awaitable, Callable, Optional

from fastapi import APIRouter, Depends, HTTPException

from backend.schemas import GeneratedBy, Outfit, OutfitsRequest, OutfitsResponse
from backend.services import catalog, gemini, supabase, veri
from training import reward
from training.prompt import build_request
from training.retrieval import _allowed, _score

router = APIRouter()
log = logging.getLogger(__name__)

CANDIDATES = 50
MIN_OUTFITS = 2
UPGRADE_RANGE = 150.0
MAX_SWAPS = 3

CHAIN: list[tuple[GeneratedBy, Callable[[list[dict]], Awaitable[Optional[str]]]]] = [
    ("our-llama", lambda messages: veri.chat("OUR_LLAMA", messages)),
    ("base-llama", lambda messages: veri.chat("BASE_LLAMA", messages)),
    ("gemini", lambda messages: gemini.chat(messages)),
]


@router.post("/outfits")
async def outfits(req: OutfitsRequest, user_id: str = Depends(supabase.current_user)) -> OutfitsResponse:
    profile = await supabase.get_profile(user_id)
    if profile is None:
        raise HTTPException(404, "Make a style profile first")
    items = {item_id: item.model_dump() for item_id, item in catalog.items().items()}
    closet = {c["id"]: c for c in profile["closet"]}

    anchor = _lookup(req.anchor.id, items, closet) if req.anchor else None

    budget_min, budget_max, wanted = req.budget_min, req.budget_max, 3
    if req.upgrade_of:
        current = round(sum(_lookup(i, items, closet)["price"] for i in req.upgrade_of), 2)
        budget_min, budget_max, wanted = round(current + 0.01, 2), current + UPGRADE_RANGE, 1

    messages, columns = build_request(
        profile, list(items.values()), occasion=req.occasion, budget_min=budget_min, budget_max=budget_max,
        anchor=anchor, n=CANDIDATES, max_item_price=req.max_item_price, outfits=wanted,
    )
    ctx = reward.prepare_context(columns)

    generated_by, chosen = await _generate(messages, ctx, wanted, upgrade=bool(req.upgrade_of))
    swap_pool = [i for i in items.values() if _allowed(i, profile, None, budget_max, req.max_item_price, req.occasion)]
    swap_pool.sort(key=lambda i: (-_score(i, profile), i["id"]))
    return OutfitsResponse(
        outfits=[
            _outfit(ids, why, items, closet, req.anchor.id if req.anchor else None, swap_pool, budget_min, budget_max)
            for ids, why in chosen
        ],
        generated_by=generated_by,
    )


def _lookup(item_id: str, items: dict[str, dict], closet: dict[str, dict]) -> dict:
    """A catalog item, or a closet item shaped like one (its description as the name, price 0)."""
    if item_id in items:
        return items[item_id]
    if item_id in closet:
        return {**closet[item_id], "name": closet[item_id]["description"], "price": 0.0}
    raise HTTPException(422, f"{item_id} isn't in the catalog or your closet")


async def _generate(messages, ctx, wanted: int, upgrade: bool) -> tuple[GeneratedBy, list[tuple[list[str], str]]]:
    needed = min(MIN_OUTFITS, wanted)
    best: tuple[GeneratedBy, list] | None = None
    for name, ask in CHAIN:
        for _ in range(2):
            try:
                text = await ask(messages)
            except Exception as e:  # network errors, quota, a deployment still waking
                log.warning("%s failed: %r", name, e)
                break
            if text is None:  # not configured
                break
            kept = _guard(text, ctx, upgrade)[:wanted]
            if len(kept) >= needed:
                return name, kept
            if kept and (best is None or len(kept) > len(best[1])):
                best = (name, kept)
    if best is None:
        raise HTTPException(503, "Couldn't put outfits together right now. Try again in a minute.")
    return best


def _guard(text: str, ctx: dict, upgrade: bool) -> list[tuple[list[str], str]]:
    """(item ids, reason) for each outfit in the answer that passes the reward's checks."""
    fenced = re.fullmatch(r"\s*```(?:json)?\s*(.*?)\s*```\s*", text, re.DOTALL)
    parsed = reward.parse_output(fenced.group(1) if fenced else text.strip())
    kept, seen = [], set()
    for o in parsed or []:
        key = frozenset(o["items"])
        if key in seen:
            continue
        seen.add(key)
        _, passed, breakdown = reward.score_outfit(o, ctx)
        if passed and (upgrade or (breakdown["anchor"] and breakdown["budget"])):
            kept.append((o["items"], o["reason"]))
    return kept


def _outfit(ids, why, items, closet, anchor_id, swap_pool, budget_min, budget_max) -> Outfit:
    bought = [items[i] for i in ids if i in items]
    total = round(sum(i["price"] for i in bought), 2)
    swaps = {}
    for item in bought:
        if item["id"] == anchor_id:
            continue
        others = total - item["price"]
        swaps[item["id"]] = [
            s for s in swap_pool
            if s["slot"] == item["slot"] and s["id"] not in ids
            and budget_min - 0.005 <= others + s["price"] <= budget_max + 0.005
        ][:MAX_SWAPS]
    return Outfit(
        id=uuid.uuid4().hex[:12],
        items=bought,
        owned=[closet[i] for i in ids if i in closet],
        total=total,
        reason=why,
        swaps=swaps,
    )
