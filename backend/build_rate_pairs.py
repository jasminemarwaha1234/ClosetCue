"""Build the blind A/B pairs that GET /rate/next serves (PLAN.md section 6, item 5).

    python3 -m backend.build_rate_pairs training/results/v0/base-llama.jsonl training/results/grpo/our-llama.jsonl \
        --labels v0-base v1-grpo [--prompts training/data/prompts_eval.jsonl] [--seed 0]

Both answer files come from `training.eval --out` over the same --data prompts file. Answers are joined
by their row in that file; the request comes from the row, the summary and closet from the row's
profile in training/data/profiles.jsonl, and the items from the live catalog. Each side's outfit is the
first one in its answer that the live /outfits guard keeps, so a pair shows what users would see; a row
is skipped when either side has none. Labels default to the files' names and are stored as a_model and
b_model. A seeded shuffle decides which side is a, so rebuilding gives the same file.

Writes backend/data/rate_pairs.jsonl, one {"pair": RatePair, "a_model", "b_model"} per line.
"""

import argparse
import hashlib
import json
import random
from pathlib import Path
from typing import Optional

from backend.routes.outfits import _guard, _outfit
from backend.routes.rate import PAIRS
from backend.schemas import OutfitsRequest, RatePair
from backend.services import catalog
from training import reward

DATA = Path(__file__).resolve().parents[1] / "training" / "data"


def _first_outfit(record: dict, row: dict, profile: dict, items: dict[str, dict]) -> Optional[dict]:
    """The first outfit of the answer the live guard keeps, as an Outfit dict, or None."""
    if record.get("raw") is None:
        return None
    closet = {c["id"]: c for c in profile["closet"]}
    anchor_id = row["anchor"]["id"] if row["anchor"] else None
    for ids, why in _guard(record["raw"], reward.prepare_context(row), upgrade=False):
        if all(i in items or i in closet for i in ids):  # an item dropped from the catalog since the eval
            outfit = _outfit(ids, why, items, closet, anchor_id, [], row["budget_min"], row["budget_max"])
            return outfit.model_dump()
    return None


def build_pairs(answers: tuple[list[dict], list[dict]], labels: tuple[str, str], prompts: list[dict],
                profiles: dict[str, dict], items: dict[str, dict], seed: int = 0) -> list[dict]:
    rng = random.Random(seed)
    second = {r["row"]: r for r in answers[1]}
    pairs = []
    for first in sorted(answers[0], key=lambda r: r["row"]):
        if first["row"] not in second:
            continue
        row = prompts[first["row"]]
        for record in (first, second[first["row"]]):
            if record["profile_id"] != row["profile_id"]:
                raise SystemExit(f"Row {record['row']} is {record['profile_id']} in the answers but "
                                 f"{row['profile_id']} in the prompts: use the prompts file the eval ran on")
        profile = profiles[row["profile_id"]]
        sides = [(label, _first_outfit(record, row, profile, items))
                 for label, record in zip(labels, (first, second[first["row"]]))]
        if any(outfit is None for _, outfit in sides):
            continue
        rng.shuffle(sides)
        # Opaque to the app, and the same whichever file is given first.
        key = "|".join(sorted(labels)) + f"|{first['row']}"
        pair = RatePair(
            pair_id="pair_" + hashlib.sha1(key.encode()).hexdigest()[:12],
            request=OutfitsRequest(anchor=row["anchor"], budget_min=row["budget_min"],
                                   budget_max=row["budget_max"], occasion=row["occasion"]),
            profile_summary=profile["summary"],
            a=sides[0][1],
            b=sides[1][1],
        )
        pairs.append({"pair": pair.model_dump(), "a_model": sides[0][0], "b_model": sides[1][0]})
    return pairs


def _jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("answers", nargs=2, type=Path, help="two eval.py answer files (<model>.jsonl)")
    parser.add_argument("--labels", nargs=2, help="model names to store; default: the files' names")
    parser.add_argument("--prompts", type=Path, default=DATA / "prompts_eval.jsonl")
    parser.add_argument("--profiles", type=Path, default=DATA / "profiles.jsonl")
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()

    labels = tuple(args.labels or (p.stem for p in args.answers))
    if labels[0] == labels[1]:
        parser.error(f"both files are labeled {labels[0]}: name them with --labels")
    answers = tuple(_jsonl(p) for p in args.answers)
    profiles = {p["id"]: p for p in _jsonl(args.profiles)}
    items = {i: item.model_dump() for i, item in catalog.items().items()}
    pairs = build_pairs(answers, labels, _jsonl(args.prompts), profiles, items, args.seed)

    PAIRS.parent.mkdir(exist_ok=True)
    PAIRS.write_text("".join(json.dumps(p) + "\n" for p in pairs))
    shared = {r["row"] for r in answers[0]} & {r["row"] for r in answers[1]}
    a_first = sum(p["a_model"] == labels[0] for p in pairs)
    print(f"Wrote {len(pairs)} pairs to {PAIRS} ({a_first} with {labels[0]} as a). Skipped "
          f"{len(shared) - len(pairs)} of {len(shared)} shared rows where a side had no outfit the live guard keeps.")


if __name__ == "__main__":
    main()
