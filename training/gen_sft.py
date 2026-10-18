"""Build the SFT answers for v1-sft (PLAN.md, Data step 4).

Run from the repo root:
    python -m training.gen_sft [--data training/data/prompts_train.jsonl]
        [--out training/data/sft_train.jsonl] [--max-candidates 50] [--seed 0]

Only rows with at most --max-candidates candidates are used (v1-sft trains on the 25- and
50-candidate rows, which keeps sequences short). For each one, the answer is the row's 3 best
distinct outfits (build_prompts.best_outfits), best first, each with a one-sentence reason from
a seeded template (training/reasons.py, which the live route also uses) that names 1 or 2 of
its items, the occasion and a profile style tag. A row is skipped when it has fewer than 3 outfits, when any of them breaks a rule the prompt states (a
missing anchor, an incomplete outfit, a total outside the budget), or when the answer scores under
MIN_SHARE of the row's best possible reward. Every reason is checked with the reward's own reason
rule; an outfit whose templated reasons all fail falls back to naming an item by id.

Each output row is {"messages": [system, user, assistant]}, Veri's sft_text chat format, with the
assistant content exactly the JSON the model should emit.
"""

import argparse
import json
import random
from collections import Counter
from pathlib import Path

from training import reward
from training.build_prompts import best_outfits
from training.reasons import PAIR_TEMPLATES, reason

HERE = Path(__file__).parent
MIN_SHARE = 0.95


def answer(row: dict, rng: random.Random) -> tuple[str | None, str]:
    """(the assistant's JSON answer, "ok") or (None, why the row is skipped)."""
    ctx = reward.prepare_context(row)
    outfits = best_outfits(ctx)
    if len(outfits) < reward.OUTFITS_WANTED:
        return None, "fewer than 3 outfits"
    for o in outfits:
        _, passed, breakdown = reward.score_outfit(o, ctx)
        if not passed or min(breakdown["anchor"], breakdown["complete"]) < 1:
            return None, "a top-3 outfit breaks a stated rule"
    best = reward.score_completion(json.dumps({"outfits": outfits}), ctx)
    templates = rng.sample(PAIR_TEMPLATES, len(outfits))
    answers = []
    for n, (o, template) in enumerate(zip(outfits, templates)):
        others = {i for m, other in enumerate(outfits) if m != n for i in other["items"]}
        answers.append({"items": o["items"],
                        "reason": reason(o["items"], others, ctx, row["profile_style_tags"], rng, template)})
    text = reward.format_output(answers)
    if reward.score_completion(text, ctx) < MIN_SHARE * best:
        return None, "scores under 95% of the best possible"
    return text, "ok"


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
