"""Build the SFT answers for v1-sft (PLAN.md, Data step 4).

Run from the repo root:
    python -m training.gen_sft [--data training/data/prompts_train.jsonl]
        [--out training/data/sft_train.jsonl] [--max-candidates 50] [--seed 0]

Only rows with at most --max-candidates candidates are used (v1-sft trains on the 25- and
50-candidate rows, which keeps sequences short). For each one, the answer is the row's 3 best
distinct outfits (build_prompts.best_outfits), best first, each with its real total and a one-sentence reason from
a seeded template that names 1 or 2 of its items, the occasion and a profile style tag. A row is
skipped when it has fewer than 3 outfits, when any of them breaks a rule the prompt states (a
missing anchor, an incomplete outfit, a total outside the budget), or when the answer scores under
MIN_SHARE of the row's best possible reward. Every reason is checked with the reward's own reason
rule; an outfit whose templated reasons all fail falls back to naming an item by id.

Each output row is {"messages": [system, user, assistant]}, Veri's sft_text chat format, with the
assistant content exactly the JSON the model should emit.
"""

import argparse
import json
import random
import re
from collections import Counter
from pathlib import Path

from training import reward
from training.build_prompts import best_outfits

HERE = Path(__file__).parent
MIN_SHARE = 0.95
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


def answer(row: dict, rng: random.Random) -> tuple[str | None, str]:
    """(the assistant's JSON answer, "ok") or (None, why the row is skipped)."""
    ctx = reward.prepare_context(row)
    outfits = best_outfits(ctx)
    if len(outfits) < reward.OUTFITS_WANTED:
        return None, "fewer than 3 outfits"
    for o in outfits:
        breakdown = reward.score_outfit(o, ctx)[2]
        if min(breakdown["anchor"], breakdown["complete"], breakdown["budget"]) < 1:
            return None, "a top-3 outfit breaks a stated rule"
    best = reward.score_completion(json.dumps({"outfits": outfits}), ctx)
    templates = rng.sample(PAIR_TEMPLATES, len(outfits))
    answers = []
    for n, (o, template) in enumerate(zip(outfits, templates)):
        others = {i for m, other in enumerate(outfits) if m != n for i in other["items"]}
        answers.append({"items": o["items"], "total": o["total"],
                        "reason": _reason(o["items"], others, ctx, row["profile_style_tags"], rng, template)})
    text = json.dumps({"outfits": answers}, separators=(",", ":"), ensure_ascii=False)
    if reward.score_completion(text, ctx) < MIN_SHARE * best:
        return None, "scores under 95% of the best possible"
    return text, "ok"


def _reason(ids: list[str], others: set[str], ctx: dict, tags: list[str], rng: random.Random,
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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, default=HERE / "data" / "prompts_train.jsonl")
    parser.add_argument("--out", type=Path, default=HERE / "data" / "sft_train.jsonl")
    parser.add_argument("--max-candidates", type=int, default=50, help="skip rows with more candidates")
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()

    rows = [json.loads(line) for line in args.data.read_text().splitlines() if line.strip()]
    kept, skipped = [], Counter()
    for n, row in enumerate(rows):
        if len(row["candidates"]) - bool(row["anchor"]) > args.max_candidates:
            skipped[f"over {args.max_candidates} candidates"] += 1
            continue
        text, why = answer(row, random.Random(f"{args.seed}-{n}"))
        if text is None:
            skipped[why] += 1
            continue
        kept.append({"messages": row["messages"] + [{"role": "assistant", "content": text}]})
    args.out.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in kept))
    print(f"wrote {len(kept)} of {len(rows)} rows to {args.out}; skipped {dict(skipped)}")


if __name__ == "__main__":
    main()
