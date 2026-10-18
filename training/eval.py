"""Evaluate one model on held-out prompts (PLAN.md section 6, NEXT_STEPS.md steps 6 and 10).

    python -m training.eval --model gemini --data training/data/prompts_eval.jsonl --limit 20 --out training/results

Each row of --data is a prompt from build_prompts.py: {"messages": [system, user], the
reward.CONTEXT_COLUMNS, "profile_id"}. The model answers the first --limit rows once each, in order,
with a pause between calls, through the same clients the live /outfits route uses.

Answers are scored on the raw text the way GRPO scores them (reward.score_completion, so fenced JSON
gets 0), and against the row's best possible reward (build_prompts.best_outfits), since some rows
can't reach the maximum. They also go through the live route's guard, which strips fences and uses
real totals, to count the outfits users would see.

Writes <out>/<model>.jsonl (one record per answer, as it arrives) and <out>/<model>_summary.json, and
prints the summary. A 429 after every fallback model means the quota is gone: the run stops and the
summary covers the answers so far.
"""

import argparse
import asyncio
import json
import math
import random
import statistics
import time
from pathlib import Path

from backend.routes.outfits import CHAIN, _guard
from training import reward
from training.build_prompts import best_outfits

MODELS = dict(CHAIN)
DELAY = 4.0  # seconds between calls, under the Gemini free tier's per-minute limit
MAX_REWARD = 7.5


def score_answer(text: str, row: dict) -> dict:
    """The answer scored the way training scores it, plus what the live guard would keep."""
    ctx = reward.prepare_context(row)
    outfits = reward.parse_output(text)
    scored = []
    for o in outfits or []:
        score, passed, breakdown = reward.score_outfit(o, ctx)
        real = round(sum(ctx["by_id"][i]["price"] for i in o["items"] if i in ctx["by_id"]), 2)
        in_budget = passed and float(ctx["budget_min"]) - 0.005 <= real <= float(ctx["budget_max"]) + 0.005
        scored.append({**o, "score": score, "passed": passed, "breakdown": breakdown,
                       "real_total": real, "in_budget": in_budget})
    return {
        "fenced": text.lstrip().startswith("```"),
        "valid_json": outfits is not None,
        "outfits": scored,
        "reward": reward.score_completion(text, ctx),
        "live_kept": len(_guard(text, ctx, upgrade=False)),
    }


def best_possible(row: dict) -> float:
    """The reward of the best answer the row allows; 0 when no complete outfit fits."""
    ctx = reward.prepare_context(row)
    return reward.score_completion(json.dumps({"outfits": best_outfits(ctx)}), ctx)


def _quota(e: Exception) -> bool:
    """A 429: gemini.chat raises one only after every model is out; veri.chat raises it as is."""
    status = getattr(e, "code", None) or getattr(getattr(e, "response", None), "status_code", None)
    return status == 429


async def run(model: str, rows: list[dict], path: Path) -> tuple[list[dict], str | None]:
    """(records, why the run stopped early or None). Records are written to path as they arrive."""
    ask = MODELS[model]
    records, stopped = [], None
    with path.open("w") as f:
        for n, row in enumerate(rows):
            if n:
                await asyncio.sleep(DELAY)
            start = time.monotonic()
            try:
                text, error = await ask(row["messages"]), None
            except Exception as e:  # network errors, timeouts, a deployment still waking
                if _quota(e):
                    stopped = f"quota exhausted at row {n}: {e!r}"
                    break
                text, error = None, repr(e)
            if text is None and error is None:
                stopped = f"{model} isn't configured in backend/.env"
                break
            record = {
                "row": n, "profile_id": row.get("profile_id"), "candidates": len(reward.prepare_context(row)["by_id"]),
                "raw": text, "latency": round(time.monotonic() - start, 2), "error": error,
                "best_possible": best_possible(row),
            }
            if text is not None:
                record.update(score_answer(text, row))
            records.append(record)
            f.write(json.dumps(record) + "\n")
            f.flush()
    return records, stopped


def summarize(records: list[dict], model: str, stopped: str | None) -> dict:
    """Rates over answers that came back (errors are counted apart); outfit rates over the outfits
    in valid answers, where an outfit with an invented item fails every check. The % of best
    possible averages each answer's reward over its row's best, skipping rows where that is 0."""
    answered = [r for r in records if r["error"] is None]
    outfits = [o for r in answered for o in r["outfits"]]
    n = len(answered)
    latencies = sorted(r["latency"] for r in answered)
    mean_reward = statistics.fmean(r["reward"] for r in answered) if answered else None
    winnable = [r for r in answered if r["best_possible"]]

    def pct(count, total):
        return round(100 * count / total, 1) if total else None

    return {
        "model": model,
        "answers": n,
        "errors": len(records) - n,
        "stopped": stopped,
        "valid_json_pct": pct(sum(r["valid_json"] for r in answered), n),
        "fenced": sum(r["fenced"] for r in answered),
        "invented_pct": pct(sum(any(not o["passed"] for o in r["outfits"]) for r in answered), n),
        "valid_no_invented_pct": pct(sum(r["valid_json"] and all(o["passed"] for o in r["outfits"]) for r in answered), n),
        "outfits": len(outfits),
        "complete_pct": pct(sum(o["breakdown"].get("complete") == 1.0 for o in outfits), len(outfits)),
        "within_budget_pct": pct(sum(o["in_budget"] for o in outfits), len(outfits)),
        "anchor_pct": pct(sum(o["breakdown"].get("anchor") == 1.0 for o in outfits), len(outfits)),
        "mean_reward": round(mean_reward, 3) if answered else None,
        "mean_reward_of_max_pct": pct(mean_reward, MAX_REWARD) if answered else None,
        "mean_best_possible": round(statistics.fmean(r["best_possible"] for r in answered), 3) if answered else None,
        "mean_reward_of_best_pct": pct(sum(r["reward"] / r["best_possible"] for r in winnable), len(winnable)),
        "live_outfits_pct": pct(sum(r["live_kept"] for r in answered), reward.OUTFITS_WANTED * n),
        "live_answers_ok_pct": pct(sum(r["live_kept"] >= 2 for r in answered), n),
        "latency_median_s": round(statistics.median(latencies), 2) if latencies else None,
        "latency_p90_s": latencies[math.ceil(0.9 * n) - 1] if latencies else None,
    }


LABELS = [
    ("answers", "Answers"),
    ("errors", "Errors (not scored)"),
    ("valid_json_pct", "Valid JSON %"),
    ("fenced", "Fenced in ``` (reward 0)"),
    ("invented_pct", "Answers with an invented item %"),
    ("valid_no_invented_pct", "Valid JSON, nothing invented %"),
    ("outfits", "Outfits in valid answers"),
    ("complete_pct", "Complete outfit %"),
    ("within_budget_pct", "Within budget (real prices) %"),
    ("anchor_pct", "Anchor included %"),
    ("mean_reward", f"Mean reward (max {MAX_REWARD})"),
    ("mean_reward_of_max_pct", "Mean reward, % of max"),
    ("mean_best_possible", "Mean best possible reward"),
    ("mean_reward_of_best_pct", "Mean reward, % of each row's best"),
    ("live_outfits_pct", "Outfits the live guard keeps %"),
    ("live_answers_ok_pct", "Answers with 2+ kept (no retry) %"),
    ("latency_median_s", "Median latency (s)"),
    ("latency_p90_s", "p90 latency (s)"),
]


def report(summary: dict, records: list[dict]) -> str:
    lines = [f"Model: {summary['model']}"]
    if summary["stopped"]:
        lines.append(f"Stopped early: {summary['stopped']}")
    lines += [f"  {label:<36} {summary[key]}" for key, label in LABELS]
    answered = [r for r in records if r["error"] is None]
    if answered:
        picks = [("Random", r) for r in random.Random(0).sample(answered, min(3, len(answered)))]
        picks.append(("Lowest reward", min(answered, key=lambda r: r["reward"])))
        for title, r in picks:
            lines += ["", f"--- {title}: row {r['row']} ({r['profile_id']}), reward {r['reward']} "
                          f"of {r['best_possible']} possible, "
                          f"live guard keeps {r['live_kept']}, {r['latency']}s", r["raw"]]
            lines += [f"  outfit {o['items']}: score {o['score']}, {o['breakdown']}" for o in r["outfits"]]
    for r in records:
        if r["error"]:
            lines.append(f"Error on row {r['row']}: {r['error']}")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--model", required=True, choices=sorted(MODELS))
    parser.add_argument("--data", required=True, type=Path)
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()

    rows = [json.loads(line) for line in args.data.read_text().splitlines() if line.strip()][:args.limit]
    args.out.mkdir(parents=True, exist_ok=True)
    records, stopped = asyncio.run(run(args.model, rows, args.out / f"{args.model}.jsonl"))
    summary = summarize(records, args.model, stopped)
    (args.out / f"{args.model}_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(report(summary, records))


if __name__ == "__main__":
    main()
