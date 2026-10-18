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
    candidates          [{"id", "slot", "price", "colors", "formality", "style_tags", "pattern"?,
                        "fit"?, "season"?, "name"?}], the anchor included; closet items cost 0
    profile_style_tags  [str]
    profile_fits        [str]
    profile_avoid       [str], style tags or colors
"""

import json
import re

# Copied from training/vocab.py because Veri receives this file alone.
# test_reward.py fails if the copies drift.
NEUTRALS = frozenset({
    "white", "cream", "beige", "tan", "khaki",
    "brown", "gray", "charcoal", "black",
})
VERSATILES = frozenset({
    "navy", "denim", "olive", "blue", "forest-green", "muted-green",
    "burgundy", "light-blue", "lilac", "gold", "silver",
})
ACCENTS = frozenset({
    "yellow", "orange", "red", "pink", "purple",
})
COLOR_COMPATIBILITY = {
    "neutral": {"neutral": 1.0, "versatile": 1.0, "accent": 0.9},
    "versatile": {"neutral": 1.0, "versatile": 0.9, "accent": 0.75},
    "accent": {"neutral": 0.9, "versatile": 0.75, "accent": 0.6},
}
STYLE_TAGS = (
    "minimal", "old-money", "western", "preppy",
    "streetwear", "techwear", "workwear", "outdoors", "athleisure",
    "bohemian", "y2k", "goth", "coastal", "sporty",
    "clean-girl", "soft-girl", "grunge",
)
OCCASION_FORMALITY = {
    "formal": (4, 5),
    "semi-formal": (4, 5),
    "work": (3, 4),
    "everyday": (2, 4),
    "party": (2, 4),
    "casual": (1, 3),
    "athletic": (1, 2),
    "comfy": (1, 2),
}
LOUD_PATTERNS = frozenset({"check", "large-print", "graphic"})
OCCASION_RULES = {
    "athletic": {
        "slots": ("top", "bottom", "dress", "shoes"),
        "tags": ("sporty", "athleisure"),
        "exclude": (
            "jeans", "denim", "chino", "trouser", "skirt", "dress shirt", "oxford", "blazer",
            "loafer", "boot", "slipper", "clog", "flip flop", "slide", "sandal", "heel",
        ),
    },
}

COLOR_GROUP = {
    **{c: "neutral" for c in NEUTRALS},
    **{c: "versatile" for c in VERSATILES},
    **{c: "accent" for c in ACCENTS},
}

OUTFITS_WANTED = 3
MAX_REASON_WORDS = 40
CONTEXT_COLUMNS = (
    "occasion", "budget_min", "budget_max", "anchor", "candidates",
    "profile_style_tags", "profile_fits", "profile_avoid",
)
_NAME_STOPWORDS = frozenset({"with", "from", "mens", "women", "womens", "unisex", "the", "and"})
# A period after these, or before a lowercase word, doesn't end a sentence ("Dr. Martens").
_NOT_A_BREAK = re.compile(r"\b(?:Dr|Mr|Mrs|Ms|St|Jr|Co|Inc|vs)\.|\.(?=\s+[a-z])")


def format_output(outfits):
    """The exact JSON the model is trained to emit for [{"items", "reason"}], parse_output's inverse."""
    answers = [{"items": o["items"], "reason": o["reason"]} for o in outfits]
    return json.dumps({"outfits": answers}, separators=(",", ":"), ensure_ascii=False)


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
    parsed = []
    for o in outfits:
        # A stray "total" (the v1 schema, or a model that adds one anyway) is ignored.
        if not isinstance(o, dict) or set(o) - {"total"} != {"items", "reason"}:
            return None
        items, reason = o["items"], o["reason"]
        if not isinstance(items, list) or not items or not all(isinstance(i, str) for i in items):
            return None
        if not isinstance(reason, str):
            return None
        parsed.append({"items": items, "reason": reason})
    return parsed


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
    ctx["profile_fits"] = set(ctx["profile_fits"] or [])
    ctx["profile_avoid"] = set(ctx["profile_avoid"] or [])
    return ctx


def score_outfit(outfit, ctx):
    """(score, gates_passed, breakdown) for one parsed outfit. Max 7.5; 0 when a gate fails: an
    invented item, or a real total (from the candidates' prices) outside the budget."""
    if "by_id" not in ctx:
        ctx = prepare_context(ctx)
    by_id = ctx["by_id"]
    invented = [i for i in outfit["items"] if i not in by_id]
    if invented:
        return 0.0, False, {"invented": invented}

    items = [by_id[i] for i in outfit["items"]]
    if not _budget(items, ctx["budget_min"], ctx["budget_max"]):
        return 0.0, False, {"outside_budget": round(sum(float(it["price"]) for it in items), 2)}
    anchor = ctx["anchor"]
    others = [it for it in items if not anchor or it["id"] != anchor["id"]]
    breakdown = {
        "anchor": 1.0 if not anchor or anchor["id"] in outfit["items"] else 0.0,
        "complete": _complete(outfit["items"], items),
        "budget": 1.0,  # the budget is a gate above; the point keeps the max at 7.5
        "color": _color(items),
        "pattern": _pattern(items),
        "season": _season(items),
        "formality": _formality(items, ctx["occasion"]),
        "profile": _profile(others, ctx["profile_style_tags"], ctx["profile_fits"], ctx["profile_avoid"]),
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


def _budget(items, lo, hi):
    real = round(sum(float(it["price"]) for it in items), 2)
    return 1.0 if float(lo) - 0.005 <= real <= float(hi) + 0.005 else 0.0


def _color(items):
    colors = sorted({c for it in items for c in it["colors"]})
    return min(
        (COLOR_COMPATIBILITY[COLOR_GROUP[a]][COLOR_GROUP[b]]
         for i, a in enumerate(colors) for b in colors[i + 1:]),
        default=1.0,
    )


def _pattern(items):
    loud = sum(1 for it in items if it.get("pattern") in LOUD_PATTERNS)
    return 0.5 if loud <= 1 else 0.0


def _season(items):
    seasons = [set(it["season"]) for it in items if it.get("season")]
    if len(seasons) < 2:
        return 0.5
    return 0.5 if set.intersection(*seasons) else 0.0


def _formality(items, occasion):
    if occasion not in OCCASION_FORMALITY:
        return 0.0
    lo, hi = OCCASION_FORMALITY[occasion]
    levels = [int(it["formality"]) for it in items]
    coherent = max(levels) - min(levels) <= 1
    fits = all(lo <= f <= hi for f in levels) and all(occasion_allows(it, occasion) for it in items)
    return 1.0 if coherent and fits else 0.0


def occasion_allows(item, occasion):
    """Whether the item passes the occasion's OCCASION_RULES entry (the formality range aside).
    Retrieval, the prompt builder's anchors and the formality check all use this."""
    rule = OCCASION_RULES.get(occasion)
    if not rule or item["slot"] not in rule["slots"]:
        return True
    name = (item.get("name") or item.get("description") or "").lower()
    return bool(set(rule["tags"]) & set(item["style_tags"])) and not any(
        re.search(rf"\b{re.escape(word)}s?\b", name) for word in rule["exclude"])


def _profile(items, tags, fits, avoid):
    if any(avoid & (set(it["style_tags"]) | set(it["colors"])) for it in items):
        return 0.0
    if not items:
        return 1.0
    total = 0.0
    for it in items:
        checks = []
        if tags:
            checks.append(1.0 if tags & set(it["style_tags"]) else 0.0)
        if fits and it.get("fit"):
            checks.append(1.0 if it["fit"] in fits else 0.0)
        total += sum(checks) / len(checks) if checks else 1.0
    return total / len(items)


def _words(text):
    return {w.rstrip("s") for w in re.findall(r"[a-z][a-z'-]*", text.lower())}


def _name_words(item):
    skip = set(COLOR_GROUP) | set(STYLE_TAGS) | _NAME_STOPWORDS
    return {w for w in _words(item.get("name") or "") if len(w) >= 4 and w not in skip}


def _reason(reason, ids, items):
    text = reason.strip()
    if not text or "\n" in text or len(text.split()) > MAX_REASON_WORDS:
        return 0.0
    if len([s for s in re.split(r"[.!?]+(?:\s+|$)", _NOT_A_BREAK.sub("", text)) if s.strip()]) != 1:
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
