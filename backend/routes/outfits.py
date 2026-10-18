# POST /outfits: outfits for the user's profile, occasion, budget and anchor (PLAN.md sections 4 and 5).
#
# Retrieval picks the candidates, a model chooses outfits from them, and the reward's checks
# guard every answer: an outfit is dropped when it fails a gate (bad JSON, an invented item), misses
# the anchor, or is outside the budget (an over-budget outfit first gets one swap to fit, _repair).
# Totals come from catalog prices; the model doesn't state one. Reasons are rewritten from the final
# items with gen_sft's templates (training/reasons.py), since Llama's often name items it didn't pick;
# Gemini's reasons are kept unless a repair swapped one of its items.
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
from training import reasons, reward
from training.prompt import build_request
from training.retrieval import _allowed, _score

router = APIRouter()
log = logging.getLogger(__name__)

CANDIDATES = 50
MIN_OUTFITS = 2
UPGRADE_RANGE = 150.0
MAX_SWAPS = 3

# Each model is asked with (messages, the ids it may use, how many outfits).
CHAIN: list[tuple[GeneratedBy, Callable[[list[dict], list[str], int], Awaitable[Optional[str]]]]] = [
    ("our-llama", lambda messages, ids, n: veri.chat("OUR_LLAMA", messages, ids, n)),
    ("base-llama", lambda messages, ids, n: veri.chat("BASE_LLAMA", messages, ids, n)),
    ("gemini", lambda messages, ids, n: gemini.chat(messages)),
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
        # Pricier than both the current outfit and budget_max, so checkout's mandate refuses it (PLAN.md section 8).
        current = round(sum(_lookup(i, items, closet)["price"] for i in req.upgrade_of), 2)
        floor = max(current, req.budget_max)
        budget_min, budget_max, wanted = round(floor + 0.01, 2), floor + UPGRADE_RANGE, 1

    messages, columns = build_request(
        profile, list(items.values()), occasion=req.occasion, budget_min=budget_min, budget_max=budget_max,
        anchor=anchor, n=CANDIDATES, max_item_price=req.max_item_price, outfits=wanted,
    )
    ctx = reward.prepare_context(columns)

    swap_pool = [i for i in items.values() if _allowed(i, profile, None, budget_max, req.max_item_price, req.occasion)]
    swap_pool.sort(key=lambda i: (-_score(i, profile), i["id"]))
    generated_by, chosen = await _generate(messages, ctx, wanted, upgrade=bool(req.upgrade_of), swap_pool=swap_pool,
                                           style_tags=profile["style_tags"])
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


async def _generate(messages, ctx, wanted: int, upgrade: bool, swap_pool: list[dict],
                    style_tags: list[str]) -> tuple[GeneratedBy, list[tuple[list[str], str]]]:
    needed = min(MIN_OUTFITS, wanted)
    best: tuple[GeneratedBy, list] | None = None
    for name, ask in CHAIN:
        for _ in range(2):
            try:
                text = await ask(messages, list(ctx["by_id"]), wanted)
            except Exception as e:  # network errors, quota, a deployment still waking
                log.warning("%s failed: %r", name, e)
                break
            if text is None:  # not configured
                break
            kept = _guard(text, ctx, upgrade, swap_pool, style_tags, keep_reasons=name == "gemini")[:wanted]
            if len(kept) >= needed:
                return name, kept
            if kept and (best is None or len(kept) > len(best[1])):
                best = (name, kept)
    if best is None:
        raise HTTPException(503, "Couldn't put outfits together right now. Try again in a minute.")
    return best


def _guard(text: str, ctx: dict, upgrade: bool, swap_pool: list[dict] = (), style_tags: list[str] = (),
           keep_reasons: bool = True) -> list[tuple[list[str], str]]:
    """(item ids, reason) for each outfit in the answer that passes the reward's checks. An outfit
    over budget_max first gets its priciest swappable item replaced (_repair), when that fits. The
    reason is templated from the final items unless keep_reasons and nothing was swapped."""
    fenced = re.fullmatch(r"\s*```(?:json)?\s*(.*?)\s*```\s*", text, re.DOTALL)
    parsed = reward.parse_output(fenced.group(1) if fenced else text.strip())
    if upgrade:  # an upgrade only has to cost more than the outfit it replaces (budget_min)
        ctx = {**ctx, "budget_max": float("inf")}
    kept, seen = [], set()
    for o in parsed or []:
        key = frozenset(o["items"])
        if key in seen:
            continue
        seen.add(key)
        _, passed, breakdown = reward.score_outfit(o, ctx)
        used = ctx
        if breakdown.get("outside_budget", 0) > ctx["budget_max"]:
            repaired = _repair(o, ctx, swap_pool)
            if repaired is None or frozenset(repaired[0]["items"]) in seen:
                continue
            o, used = repaired
            seen.add(frozenset(o["items"]))
            _, passed, breakdown = reward.score_outfit(o, used)
        if passed and (upgrade or breakdown["anchor"]):
            why = o["reason"] if keep_reasons and used is ctx else reasons.describe(o["items"], used, style_tags)
            kept.append((o["items"], why))
    return kept


def _repair(outfit: dict, ctx: dict, swap_pool: list[dict]) -> tuple[dict, dict] | None:
    """(the outfit with its priciest item that isn't the anchor or owned swapped for the best
    same-slot alternative that brings the total into the budget, ctx knowing that item), or None
    when there is no such swap. Every item is known: ctx gates invented items before the budget."""
    by_id, anchor = ctx["by_id"], ctx["anchor"]
    ids = outfit["items"]
    swappable = [by_id[i] for i in ids if not i.startswith("closet_") and (not anchor or i != anchor["id"])]
    if not swappable:
        return None
    priciest = max(swappable, key=lambda item: item["price"])
    total = sum(by_id[i]["price"] for i in ids)
    alternatives = _alternatives(priciest, ids, total, swap_pool, ctx["budget_min"], ctx["budget_max"])
    if not alternatives:
        return None
    swap = alternatives[0]
    repaired = {**outfit, "items": [swap["id"] if i == priciest["id"] else i for i in ids]}
    return repaired, {**ctx, "by_id": {**by_id, swap["id"]: swap}}


def _alternatives(item, ids, total, swap_pool, budget_min, budget_max) -> list[dict]:
    """Items from swap_pool that can replace item, in the pool's order, keeping the total in budget."""
    others = total - item["price"]
    return [
        s for s in swap_pool
        if s["slot"] == item["slot"] and s["id"] not in ids
        and budget_min - 0.005 <= others + s["price"] <= budget_max + 0.005
    ]


def _outfit(ids, why, items, closet, anchor_id, swap_pool, budget_min, budget_max) -> Outfit:
    bought = [items[i] for i in ids if i in items]
    total = round(sum(i["price"] for i in bought), 2)
    swaps = {}
    for item in bought:
        if item["id"] == anchor_id:
            continue
        swaps[item["id"]] = _alternatives(item, ids, total, swap_pool, budget_min, budget_max)[:MAX_SWAPS]
    return Outfit(
        id=uuid.uuid4().hex[:12],
        items=bought,
        owned=[closet[i] for i in ids if i in closet],
        total=total,
        reason=why,
        swaps=swaps,
    )
