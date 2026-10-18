"""The outfit prompt (PLAN.md section 5, Task): the messages the model sees for one request.

Used by the training prompt builder and the live /outfits route, so training prompts and live
prompts are byte-identical. Works on plain dicts: the profile is shaped like backend/schemas.py's
StyleProfile, and the anchor and candidates like retrieval's items (id, name, slot, price, colors,
formality, style_tags). A closet anchor has a closet_<n> id and price 0.
"""

from training.retrieval import format_candidates
from training.vocab import OCCASION_FORMALITY

SYSTEM = (
    "You are a personal stylist. You build outfits only from the items you are given, and you "
    "answer with strict JSON and nothing else: no code fences, no text before or after it."
)


def render_prompt(
    profile: dict,
    *,
    occasion: str,
    budget_min: float,
    budget_max: float,
    anchor: dict | None,
    candidates: list[dict],
    outfits: int = 3,
) -> list[dict]:
    low, high = OCCASION_FORMALITY[occasion]
    formality = f"{low}" if low == high else f"{low}-{high}"
    if anchor is None:
        anchor_line = "Anchor: none."
    else:
        owned = " (they own it; it costs $0)" if anchor["id"].startswith("closet_") else ""
        anchor_line = f"Anchor{owned}, which every outfit must include:\n{format_candidates([anchor])}"
    count = "exactly 1 outfit" if outfits == 1 else f"exactly {outfits} different outfits"

    user = f"""Style profile:
Summary: {profile["summary"]}
Style tags: {_list(profile["style_tags"])}
Colors they wear: {_list(profile["colors"])}
Fits: {_list(profile["fits"])}
Avoid: {_list(profile["avoid"])}

Occasion: {occasion} (formality {formality})
Budget for the catalog items: ${budget_min:.2f} to ${budget_max:.2f}
{anchor_line}

Candidates (id | name | slot | price | colors | formality | style tags):
{format_candidates(candidates)}

Build {count}. Each outfit uses only the anchor and candidate ids above, and `items` lists every piece, the anchor included. It has a top and a bottom, or a dress with neither, plus one pair of shoes, at most one outerwear, and any accessories. Every item's formality fits the occasion. `total` is the sum of the catalog items' prices and must be inside the budget. `reason` is one sentence of at most 40 words that names at least one item.

Reply with only this JSON:
{{"outfits": [{{"items": ["<id>", "<id>"], "total": <number>, "reason": "<one sentence>"}}]}}"""
    return [{"role": "system", "content": SYSTEM}, {"role": "user", "content": user}]


def _list(values: list[str]) -> str:
    return ", ".join(values) or "none"
