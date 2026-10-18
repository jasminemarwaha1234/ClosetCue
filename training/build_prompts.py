"""Build the outfit prompts for training and eval (PLAN section 5, Data).

Run from the repo root:
    python -m training.build_prompts [--profiles training/data/profiles.jsonl]
        [--catalog training/catalog.json] [--per-profile 2] [--eval-share 0.25] [--seed 0]
        [--out-dir training/data]

Profiles are split into train and eval first (eval_share of them, rounded, go to eval), so no
profile has prompts on both sides. Each side gets per_profile prompts per profile, in rounds that
visit every profile once in a shuffled order (so eval.py's --limit rows come from different
profiles), with the anchor kinds (ANCHOR_MIX) and candidate list sizes (SIZES) in exact
proportions, shuffled. The occasion is one of the profile's occasions, and the budget is the
profile's. An anchor is drawn from the items whose formality is inside the occasion's range: a
catalog anchor also passes retrieval's filters for the profile and costs at most
ANCHOR_BUDGET_SHARE of budget_max (so the rest of the outfit fits), a closet anchor comes from the
profile's closet. When none qualifies the row has no anchor. Everything comes from one seeded random.Random, so the same inputs give the same files.

Each row of prompts_train.jsonl and prompts_eval.jsonl is
    {"messages": [system, user], <reward.CONTEXT_COLUMNS>, "profile_id": str}
built by prompt.build_request, the same function the live /outfits route uses.
"""

import argparse
import itertools
import json
import random
from pathlib import Path

from training import reward
from training.prompt import build_request
from training.retrieval import _allowed
from training.vocab import OCCASION_FORMALITY

HERE = Path(__file__).parent
ANCHOR_MIX = {"catalog": 0.45, "closet": 0.35, "none": 0.20}
SIZES = (25, 50, 75, 100)
ANCHOR_BUDGET_SHARE = 0.5
# best_outfits treats scores this close as equal and takes the outfit with fewer pieces, then the
# cheaper one. Every check moves the score by 0.1 or more, except the profile average, where 0.05
# is the gap between 3 of 4 and 4 of 5 matching pieces: an artifact of piece count, not a better look.
TIE = 0.05


def split_profiles(profiles: list[dict], eval_share: float, seed: int) -> tuple[list[dict], list[dict]]:
    ids = sorted(p["id"] for p in profiles)
    random.Random(f"{seed}-split").shuffle(ids)
    eval_ids = set(ids[: round(len(ids) * eval_share)])
    return [p for p in profiles if p["id"] not in eval_ids], [p for p in profiles if p["id"] in eval_ids]


def build_rows(profiles: list[dict], catalog: list[dict], per_profile: int, seed: int) -> list[dict]:
    rng = random.Random(seed)
    jobs = rng.sample(profiles, len(profiles)) * per_profile
    kinds = _in_proportion(ANCHOR_MIX, len(jobs), rng)
    sizes = _in_proportion({size: 1 for size in SIZES}, len(jobs), rng)
    return [_row(p, catalog, kind, size, rng) for p, kind, size in zip(jobs, kinds, sizes)]


def _in_proportion(weights: dict, n: int, rng: random.Random) -> list:
    """n values in the weights' proportions (largest remainder, ties in dict order), shuffled."""
    total = sum(weights.values())
    exact = {k: n * w / total for k, w in weights.items()}
    counts = {k: int(v) for k, v in exact.items()}
    for k in sorted(weights, key=lambda k: -(exact[k] - counts[k]))[: n - sum(counts.values())]:
        counts[k] += 1
    values = [k for k, count in counts.items() for _ in range(count)]
    rng.shuffle(values)
    return values


def _row(profile: dict, catalog: list[dict], kind: str, size: int, rng: random.Random) -> dict:
    occasion = rng.choice(profile["occasions"])
    low, high = OCCASION_FORMALITY[occasion]
    if kind == "catalog":
        pool = [i for i in catalog if low <= i["formality"] <= high
                and _allowed(i, profile, None, profile["budget_max"] * ANCHOR_BUDGET_SHARE, None, occasion)]
    elif kind == "closet":
        pool = [c for c in profile["closet"] if low <= c["formality"] <= high]
    else:
        pool = []
    messages, columns = build_request(
        profile, catalog, occasion=occasion, budget_min=profile["budget_min"],
        budget_max=profile["budget_max"], anchor=rng.choice(pool) if pool else None, n=size,
    )
    return {"messages": messages, **columns, "profile_id": profile["id"]}


def complete_possible(row: dict) -> bool:
    """Whether the anchor and candidates hold a top and bottom, or a dress, plus shoes, that
    together with the anchor cost at most budget_max."""
    anchor_id = row["anchor"]["id"] if row["anchor"] else None
    anchor = next((c for c in row["candidates"] if c["id"] == anchor_id), None)
    cheapest: dict[str, float] = {}
    for c in row["candidates"]:
        if c["id"] != anchor_id:
            cheapest[c["slot"]] = min(cheapest.get(c["slot"], c["price"]), c["price"])
    for base in (("top", "bottom", "shoes"), ("dress", "shoes")):
        if anchor and anchor["slot"] not in base + ("outerwear", "accessory"):
            continue
        cost = anchor["price"] if anchor else 0.0
        if all(slot in cheapest for slot in base if not anchor or slot != anchor["slot"]):
            cost += sum(cheapest[slot] for slot in base if not anchor or slot != anchor["slot"])
            if cost <= row["budget_max"]:
                return True
    return False


def best_outfits(ctx: dict, extend: int = 50) -> list[dict]:
    """The 3 highest-scoring outfits for a reward context, best first (scores within TIE count as
    equal: fewer pieces, then the lower total, goes first): every top+bottom+shoes and
    dress+shoes that can include the anchor, then the `extend` best of those with one outerwear,
    one accessory, or one of each added. Only the best bases are extended so a 100-candidate row
    (about 10,000 bases) takes about 0.2 s; on real rows, extending 1000 found nothing better."""
    anchor = ctx["anchor"]["id"] if ctx["anchor"] else None
    by_slot: dict[str, list[str]] = {}
    for item in ctx["by_id"].values():
        by_slot.setdefault(item["slot"], []).append(item["id"])
    found: dict[frozenset, tuple[float, dict]] = {}

    def add(ids: list[str]) -> None:
        if frozenset(ids) not in found:
            outfit = {"items": ids, "reason": f"Built around {ids[0]}."}
            found[frozenset(ids)] = (reward.score_outfit(outfit, ctx)[0], outfit)

    for slots in (("top", "bottom", "shoes"), ("dress", "shoes")):
        if anchor and ctx["by_id"][anchor]["slot"] in slots:
            pools = [[anchor] if s == ctx["by_id"][anchor]["slot"] else by_slot.get(s, []) for s in slots]
        else:
            pools = [by_slot.get(s, []) for s in slots] + ([[anchor]] if anchor else [])
        for ids in itertools.product(*pools):
            add(list(ids))
    bases = sorted(found.values(), key=lambda s: -s[0])[:extend]
    outerwear, accessories = by_slot.get("outerwear", []), by_slot.get("accessory", [])
    extras = [[o] for o in outerwear] + [[a] for a in accessories] + [[o, a] for o in outerwear for a in accessories]
    for _, base in bases:
        for extra in extras:
            if not set(extra) & set(base["items"]):
                add(base["items"] + extra)
    def cost(outfit: dict) -> tuple[int, float]:
        return len(outfit["items"]), sum(ctx["by_id"][i]["price"] for i in outfit["items"])

    left, best = sorted(found.values(), key=lambda s: -s[0]), []
    while left and len(best) < reward.OUTFITS_WANTED:
        near = [s for s in left if s[0] >= left[0][0] - TIE - 1e-9]
        pick = min(near, key=lambda s: cost(s[1]))
        left.remove(pick)
        best.append(pick[1])
    return best


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--profiles", type=Path, default=HERE / "data" / "profiles.jsonl")
    parser.add_argument("--catalog", type=Path, default=HERE / "catalog.json")
    parser.add_argument("--per-profile", type=int, default=2, help="prompts per profile")
    parser.add_argument("--eval-share", type=float, default=0.25, help="share of profiles held out for eval")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--out-dir", type=Path, default=HERE / "data")
    args = parser.parse_args()

    profiles = [json.loads(line) for line in args.profiles.read_text().splitlines() if line.strip()]
    catalog = json.loads(args.catalog.read_text())
    train, held_out = split_profiles(profiles, args.eval_share, args.seed)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    for name, group, seed in (("train", train, args.seed), ("eval", held_out, args.seed + 1)):
        rows = build_rows(group, catalog, args.per_profile, seed)
        out = args.out_dir / f"prompts_{name}.jsonl"
        out.write_text("".join(json.dumps(r) + "\n" for r in rows))
        anchors = [r["anchor"]["source"] if r["anchor"] else "none" for r in rows]
        print(
            f"wrote {len(rows)} prompts for {len(group)} profiles to {out}; "
            f"anchors {({k: anchors.count(k) for k in ANCHOR_MIX})}, "
            f"a complete outfit possible in {sum(map(complete_possible, rows))}"
        )


if __name__ == "__main__":
    main()
