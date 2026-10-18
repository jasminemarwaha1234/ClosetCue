"""Pick the candidate items one outfit prompt shows the model (PLAN section 5, Retrieval).

Used by the training prompt builder and the live /outfits route, so it is deterministic:
the same catalog, profile and request always give the same candidates in the same order.
Works on plain dicts shaped like backend/schemas.py's CatalogItem, ClosetItem and StyleProfile.

Rules, in order:

1. Filter. Drop an item when any of these hold:
   - it shares the anchor's slot (accessories excepted), or it is the anchor itself;
     a dress anchor also drops tops and bottoms, and a top or bottom anchor drops dresses;
   - price > budget_max - anchor price (a closet anchor costs 0);
   - price > max_item_price, when one is set;
   - its department isn't unisex and isn't in profile["departments"] (an empty list allows all);
   - the profile is men-only and the item is a dress;
   - any of its style_tags or colors is in profile["avoid"];
   - its formality is more than one level outside the occasion's range (vocab.OCCASION_FORMALITY);
   - it breaks the occasion's rule (vocab.OCCASION_RULES, checked by reward.occasion_allows).
2. Score: number of style_tags shared with the profile, plus COLOR_BONUS if any of its colors
   is one the profile wears, plus FIT_BONUS if its fit is one of profile["fits"]. Ties break by id.
3. Split n across the slots that still have items, with SLOT_WEIGHTS renormalized over them
   (largest-remainder rounding, ties in SLOTS order).
4. Inside each slot, take the best-scoring items first, then fill IMPERFECT_SHARE of the slot's
   quota (rounded) with items spread evenly across the lower-scoring half of what's left.
   Diversity cap throughout: at most DIVERSITY_CAP items in a slot share both a color and a style tag.
5. If slots ran short, fill up to n from the remaining items of every slot, best score first,
   still under the cap. Fewer than n come back only when the filters and the cap leave too few.

The result is sorted by slot, then id, so an item's position doesn't reveal its score.
"""

from training.reward import occasion_allows
from training.vocab import OCCASION_FORMALITY, SLOTS

SLOT_WEIGHTS = {
    "top": 0.25,
    "bottom": 0.25,
    "shoes": 0.20,
    "outerwear": 0.12,
    "dress": 0.10,
    "accessory": 0.08,
}
COLOR_BONUS = 0.5
FIT_BONUS = 0.5
IMPERFECT_SHARE = 0.15
DIVERSITY_CAP = 2


def retrieve(
    catalog: list[dict],
    profile: dict,
    *,
    anchor: dict | None,
    budget_max: float,
    max_item_price: float | None,
    occasion: str,
    n: int,
) -> list[dict]:
    eligible = [
        item for item in catalog
        if _allowed(item, profile, anchor, budget_max, max_item_price, occasion)
    ]
    ranked = sorted(eligible, key=lambda item: (-_score(item, profile), item["id"]))
    by_slot = {slot: [item for item in ranked if item["slot"] == slot] for slot in SLOTS}

    chosen: list[dict] = []
    for slot, quota in _quotas(by_slot, n).items():
        chosen += _pick_slot(by_slot[slot], quota)

    taken = {item["id"] for item in chosen}
    for item in ranked:
        if len(chosen) >= n:
            break
        if item["id"] not in taken and _under_cap(item, [c for c in chosen if c["slot"] == item["slot"]]):
            chosen.append(item)
            taken.add(item["id"])

    return sorted(chosen, key=lambda item: (SLOTS.index(item["slot"]), item["id"]))


def _allowed(item, profile, anchor, budget_max, max_item_price, occasion) -> bool:
    anchor_price = 0.0
    if anchor is not None:
        anchor_price = anchor.get("price", 0.0)
        if item["id"] == anchor["id"] or item["slot"] in _excluded_slots(anchor["slot"]):
            return False
    if item["price"] > budget_max - anchor_price:
        return False
    if max_item_price is not None and item["price"] > max_item_price:
        return False
    departments = profile["departments"]
    if departments and item["department"] != "unisex" and item["department"] not in departments:
        return False
    if item["slot"] == "dress" and set(departments) == {"men"}:
        return False
    avoid = set(profile["avoid"])
    if avoid & set(item["style_tags"]) or avoid & set(item["colors"]):
        return False
    low, high = OCCASION_FORMALITY[occasion]
    return low - 1 <= item["formality"] <= high + 1 and occasion_allows(item, occasion)


def _excluded_slots(anchor_slot: str) -> set[str]:
    if anchor_slot == "accessory":
        return set()
    if anchor_slot == "dress":
        return {"dress", "top", "bottom"}
    if anchor_slot in ("top", "bottom"):
        return {anchor_slot, "dress"}
    return {anchor_slot}


def _score(item: dict, profile: dict) -> float:
    score = float(len(set(item["style_tags"]) & set(profile["style_tags"])))
    if set(item["colors"]) & set(profile["colors"]):
        score += COLOR_BONUS
    if item.get("fit") in profile.get("fits", []):
        score += FIT_BONUS
    return score


def _quotas(by_slot: dict[str, list[dict]], n: int) -> dict[str, int]:
    slots = [slot for slot in SLOTS if by_slot[slot]]
    if not slots:
        return {}
    total_weight = sum(SLOT_WEIGHTS[slot] for slot in slots)
    exact = {slot: n * SLOT_WEIGHTS[slot] / total_weight for slot in slots}
    quotas = {slot: int(exact[slot]) for slot in slots}
    by_remainder = sorted(slots, key=lambda slot: (-(exact[slot] - quotas[slot]), SLOTS.index(slot)))
    for slot in by_remainder[: n - sum(quotas.values())]:
        quotas[slot] += 1
    return quotas


def _pick_slot(ranked: list[dict], quota: int) -> list[dict]:
    imperfect = round(quota * IMPERFECT_SHARE)
    picked: list[dict] = []
    for item in ranked:
        if len(picked) >= quota - imperfect:
            break
        if _under_cap(item, picked):
            picked.append(item)

    rest = [item for item in ranked if item not in picked]
    lower = rest[len(rest) // 2:]
    for item in _spread(lower, imperfect) + rest:
        if len(picked) >= quota:
            break
        if item not in picked and _under_cap(item, picked):
            picked.append(item)
    return picked


def _spread(items: list[dict], k: int) -> list[dict]:
    """k items at evenly spaced positions, so imperfect picks aren't all the very worst."""
    if k <= 0 or not items:
        return []
    step = len(items) / k
    return [items[int(i * step)] for i in range(min(k, len(items)))]


def _under_cap(item: dict, same_slot: list[dict]) -> bool:
    for color in item["colors"]:
        for tag in item["style_tags"]:
            sharing = sum(1 for other in same_slot if color in other["colors"] and tag in other["style_tags"])
            if sharing >= DIVERSITY_CAP:
                return False
    return True


def format_candidates(items: list[dict]) -> str:
    """One line per item, about 30 tokens each, for the outfit prompt. A `|` in a name becomes `/`
    so it can't read as a column break."""
    return "\n".join(
        f"{item['id']} | {item['name'].replace('|', '/')} | {item['slot']} | ${item['price']:.2f} | "
        f"{', '.join(item['colors'])} | formality {item['formality']} | {', '.join(item['style_tags'])}"
        for item in items
    )
