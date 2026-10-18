"""The one-sentence outfit reasons: gen_sft writes the SFT answers with them, and the live
/outfits route rewrites every Llama outfit's reason with them, so live reasons match training.

Each reason comes from a seeded template that names 1 or 2 of the outfit's items, the occasion
and a profile style tag, and passes the reward's reason rule (reward._reason); when no template
does, it names an item by id.
"""

import random
import re

from training import reward

OCCASIONS = {
    "formal": "a formal event",
    "semi-formal": "a semi-formal event",
    "work": "work",
    "everyday": "everyday wear",
    "party": "a party",
    "casual": "a casual day",
    "athletic": "a workout",
    "comfy": "a comfy day in",
}
# {a} and {b} are items ({A} capitalized), {style} a style tag, {a_style} it with "a" or "an".
# No template puts a singular verb after an item, since names can be plural ("your cargo pants").
PAIR_TEMPLATES = (
    "{A} and {b} keep this {style} look right for {occasion}.",
    "Pairing {a} with {b} makes {a_style} outfit that suits {occasion}.",
    "Start from {a}, add {b}, and this {style} outfit is set for {occasion}.",
    "For {occasion}, {a} with {b} stays {style} and fits the budget.",
    "Wear {a} with {b} for {a_style} look that fits {occasion}.",
    "Built around {a}, this {style} outfit adds {b} for {occasion}.",
    "{A} plus {b} give this outfit {a_style} feel for {occasion}.",
    "{A_style} take on {occasion}: {a} with {b}.",
)
SINGLE_TEMPLATES = (
    "This {style} outfit for {occasion} is built around {a}.",
    "For {occasion}, this {style} outfit is built around {a}.",
)


def describe(ids: list[str], ctx: dict, tags: list[str]) -> str:
    """The live reason for one outfit: seeded on its item ids, so the same outfit always gets
    the same sentence whatever the item order. ctx is reward.prepare_context's, knowing every item in ids."""
    ids = sorted(ids)
    rng = random.Random("|".join(ids))
    if len(ids) < 2:
        item = ctx["by_id"][ids[0]]
        return _fill(SINGLE_TEMPLATES[0], item, None, _style([item], tags), OCCASIONS[ctx["occasion"]])
    return reason(ids, set(), ctx, tags, rng, rng.choice(PAIR_TEMPLATES))


def reason(ids: list[str], others: set[str], ctx: dict, tags: list[str], rng: random.Random,
           template: str) -> str:
    """A templated sentence that passes the reward's reason rule. b is an item the other outfits
    lack when there is one, so the three reasons differ; a is the anchor or another main piece."""
    by_id, anchor = ctx["by_id"], ctx["anchor"]
    anchor_id = anchor["id"] if anchor else None
    rest = [i for i in ids if i != anchor_id]
    b = rng.choice([i for i in rest if i not in others] or rest)
    a = anchor_id or rng.choice([i for i in rest if i != b and by_id[i]["slot"] in ("top", "dress", "bottom")]
                                or [i for i in rest if i != b])
    items = [by_id[i] for i in ids]
    style = _style([by_id[a], by_id[b]], tags)
    occasion = OCCASIONS[ctx["occasion"]]
    tries = [(template, a, b)] + [(t, i, None) for t in SINGLE_TEMPLATES for i in [a, b, *ids]]
    for t, x, y in tries:
        text = _fill(t, by_id[x], by_id[y] if y else None, style, occasion)
        if reward._reason(text, ids, items) == 0.5:
            return text
    return f"Built around {a}, this {style} outfit suits {occasion}."


def _fill(template: str, a: dict, b: dict | None, style: str, occasion: str) -> str:
    a_name = _label(a)
    a_style = f"{'an' if style[0] in 'aeiou' else 'a'} {style}"
    return template.format(
        a=a_name, A=a_name[0].upper() + a_name[1:], b=_label(b) if b else "",
        style=style, a_style=a_style, A_style=a_style.capitalize(), occasion=occasion,
    )


def _label(item: dict) -> str:
    """The item's name as a sentence would say it, after "the" or "your": shouty names in title
    case, and a trailing " - color" or " | color" dropped unless only it held a word the reward's
    name check counts."""
    name = item["name"].strip()
    short = re.split(r" [-|/–] | \(", name)[0]
    if reward._name_words({"name": short}) or not reward._name_words(item):
        name = short
    if name.isupper():
        name = " ".join(w.capitalize() for w in name.split())
    if name.lower().startswith("the "):
        name = name[4:]
    return f"{'your' if item['id'].startswith('closet_') else 'the'} {name}"


def _style(named: list[dict], tags: list[str]) -> str:
    """The first profile style tag a named item carries, else the profile's first, else "polished"."""
    carried = [t for t in tags if any(t in it["style_tags"] for it in named)]
    return (carried or tags or ["polished"])[0]
