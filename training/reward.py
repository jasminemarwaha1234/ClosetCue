"""The reward: our definition of a good outfit (PLAN.md section 5).

Veri's GRPO trainer runs this file on its own, so it uses only the standard library and imports
nothing from the repo. The backend imports it as the guard (`training.reward`): `parse_output`,
then `score_outfit` on each outfit.

Per-row context arrives as extra dataset columns, one list entry per completion. Each value may be
the object itself or a JSON string of it:

    occasion            str, a key of OCCASION_FORMALITY
    budget_min          number
    budget_max          number
    anchor              null or {"source": "catalog" | "closet", "id": str}
    candidates          [{"id", "slot", "price", "colors", "formality", "style_tags", "name"?}],
                        the anchor included; closet items cost 0
    profile_style_tags  [str]
    profile_avoid       [str], style tags or colors
"""

import json
import math
import re

# Copied from training/vocab.py because Veri receives this file alone.
# test_reward.py fails if the copies drift.
NEUTRALS = frozenset({
    "white", "cream", "beige", "tan", "khaki", "brown",
    "gray", "charcoal", "black", "navy", "denim", "gold", "silver",
})
CLASHES = frozenset(frozenset(p) for p in [
    ("red", "pink"), ("red", "orange"), ("red", "purple"), ("orange", "pink"),
    ("orange", "purple"), ("green", "red"), ("yellow", "purple"), ("burgundy", "orange"),
])
STYLE_TAGS = (
    "minimal", "classic", "relaxed", "tailored", "smart-casual", "preppy",
    "streetwear", "graphic", "workwear", "outdoors", "athleisure",
    "vintage", "bohemian", "romantic", "edgy", "trendy", "logos",
)
OCCASION_FORMALITY = {
    "everyday": (1, 3),
    "work": (3, 4),
    "date": (2, 4),
    "party": (2, 4),
    "formal": (5, 5),
    "active": (1, 1),
    "wedding_guest": (4, 5),
    "interview": (4, 5),
    "brunch": (2, 3),
    "travel": (1, 2),
    "concert": (1, 3),
    "outdoors": (1, 2),
    "campus": (1, 2),
    "lounge": (1, 1),
}

OUTFITS_WANTED = 3
MAX_REASON_WORDS = 40
CONTEXT_COLUMNS = (
    "occasion", "budget_min", "budget_max", "anchor", "candidates",
    "profile_style_tags", "profile_avoid",
)
_NAME_STOPWORDS = frozenset({"with", "from", "mens", "women", "womens", "unisex", "the", "and"})


def parse_output(text):
    """The outfits if `text` is exactly the strict output schema, else None."""
    if not isinstance(text, str):
        return None
    try:
        data = json.loads(text)
    except ValueError:
        return None
    if not isinstance(data, dict) or set(data) != {"outfits"}:
        return None
    outfits = data["outfits"]
    if not isinstance(outfits, list) or not 1 <= len(outfits) <= OUTFITS_WANTED:
        return None
    for o in outfits:
        if not isinstance(o, dict) or set(o) != {"items", "total", "reason"}:
            return None
        items, total, reason = o["items"], o["total"], o["reason"]
        if not isinstance(items, list) or not items or not all(isinstance(i, str) for i in items):
            return None
        if isinstance(total, bool) or not isinstance(total, (int, float)) or not math.isfinite(total):
            return None
        if not isinstance(reason, str):
            return None
    return outfits


def _decode(value):
    if isinstance(value, str):
        try:
            return json.loads(value)
        except ValueError:
            return value  # a plain string column such as occasion
    return value


def prepare_context(row):
    """Decode a row's context columns once; score_outfit also accepts the raw row."""
    ctx = {k: _decode(row.get(k)) for k in CONTEXT_COLUMNS}
    if not isinstance(ctx["candidates"], list):
        raise ValueError("the candidates column is missing; every row needs one")
    by_id = {}
    for c in ctx["candidates"]:
        item = dict(c)
        if item["id"].startswith("closet_"):
            item["price"] = 0.0
        by_id[item["id"]] = item
    anchor = ctx["anchor"]
    if anchor and anchor["id"] not in by_id:
        raise ValueError(f"anchor {anchor['id']} is missing from candidates")
    ctx["by_id"] = by_id
    ctx["profile_style_tags"] = set(ctx["profile_style_tags"] or [])
    ctx["profile_avoid"] = set(ctx["profile_avoid"] or [])
    return ctx


def score_outfit(outfit, ctx):
    """(score, gates_passed, breakdown) for one parsed outfit. Max 6.5; 0 when a gate fails."""
    if "by_id" not in ctx:
        ctx = prepare_context(ctx)
    by_id = ctx["by_id"]
    invented = [i for i in outfit["items"] if i not in by_id]
    if invented:
        return 0.0, False, {"invented": invented}

    items = [by_id[i] for i in outfit["items"]]
    anchor = ctx["anchor"]
    others = [it for it in items if not anchor or it["id"] != anchor["id"]]
    breakdown = {
        "anchor": 1.0 if not anchor or anchor["id"] in outfit["items"] else 0.0,
        "complete": _complete(outfit["items"], items),
        "budget": _budget(items, outfit["total"], ctx["budget_min"], ctx["budget_max"]),
        "color": _color(items),
        "formality": _formality(items, ctx["occasion"]),
        "profile": _profile(others, ctx["profile_style_tags"], ctx["profile_avoid"]),
        "reason": _reason(outfit["reason"], outfit["items"], items),
    }
    return round(sum(breakdown.values()), 4), True, breakdown


def _complete(ids, items):
    if len(set(ids)) != len(ids):
        return 0.0
    count = {}
    for it in items:
        count[it["slot"]] = count.get(it["slot"], 0) + 1
    if any(n > 1 for slot, n in count.items() if slot != "accessory"):
        return 0.0
    if count.get("dress"):
        base_ok = not (count.get("top") or count.get("bottom"))
    else:
        base_ok = bool(count.get("top") and count.get("bottom"))
    return 1.0 if base_ok and count.get("shoes") else 0.0


def _budget(items, stated, lo, hi):
    real = round(sum(float(it["price"]) for it in items), 2)
    in_range = float(lo) - 0.005 <= real <= float(hi) + 0.005
    return 1.0 if in_range and abs(real - stated) <= 0.01 + 1e-9 else 0.0


def _color(items):
    accents = {c for it in items for c in it["colors"] if c not in NEUTRALS}
    if any(frozenset((a, b)) in CLASHES for a in accents for b in accents if a < b):
        return 0.0
    return {0: 1.0, 1: 1.0, 2: 0.5}.get(len(accents), 0.0)


def _formality(items, occasion):
    if occasion not in OCCASION_FORMALITY:
        return 0.0
    lo, hi = OCCASION_FORMALITY[occasion]
    levels = [int(it["formality"]) for it in items]
    coherent = max(levels) - min(levels) <= 1
    return 1.0 if coherent and all(lo <= f <= hi for f in levels) else 0.0


def _profile(items, tags, avoid):
    if any(avoid & (set(it["style_tags"]) | set(it["colors"])) for it in items):
        return 0.0
    if not items or not tags:
        return 1.0
    return sum(1 for it in items if tags & set(it["style_tags"])) / len(items)


def _words(text):
    return {w.rstrip("s") for w in re.findall(r"[a-z][a-z'-]*", text.lower())}


def _name_words(item):
    skip = NEUTRALS | set(STYLE_TAGS) | _NAME_STOPWORDS | {c for pair in CLASHES for c in pair}
    return {w for w in _words(item.get("name") or "") if len(w) >= 4 and w not in skip}


def _reason(reason, ids, items):
    text = reason.strip()
    if not text or "\n" in text or len(text.split()) > MAX_REASON_WORDS:
        return 0.0
    if len([s for s in re.split(r"[.!?]+(?:\s+|$)", text) if s.strip()]) != 1:
        return 0.0
    if any(i in text for i in ids):
        return 0.5
    said = _words(text)
    return 0.5 if any(_name_words(it) & said for it in items) else 0.0


def score_completion(text, ctx):
    """Mean over OUTFITS_WANTED slots, so missing outfits, gate failures and repeats score 0."""
    outfits = parse_output(text)
    if outfits is None:
        return 0.0
    if "by_id" not in ctx:
        ctx = prepare_context(ctx)
    seen, total = set(), 0.0
    for o in outfits:
        key = frozenset(o["items"])
        if key in seen:
            continue
        seen.add(key)
        total += score_outfit(o, ctx)[0]
    return round(total / OUTFITS_WANTED, 4)


def reward(completions, **kwargs):
    out = []
    for n, c in enumerate(completions):
        text = c if isinstance(c, str) else c[-1]["content"]
        row = {k: kwargs[k][n] for k in CONTEXT_COLUMNS if k in kwargs}
        out.append(score_completion(text, row))
    return out
