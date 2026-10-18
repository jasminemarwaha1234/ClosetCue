"""Turn build_prompts.py rows into Veri GRPO rows.

    python training/build_grpo.py IN.jsonl OUT.jsonl [--max-candidates 50] [--limit N]

Veri's GRPO trainer generates from a `prompt` column (a chat message list is fine) and passes
every other column to `reward()` as a keyword argument. Lists and objects are written as JSON
strings so the trainer's Arrow table never has to infer a schema for the candidate dicts;
reward.py decodes them.
"""

import argparse
import json


def to_grpo(row):
    out = {"prompt": row["messages"]}
    for k, v in row.items():
        if k != "messages":
            out[k] = json.dumps(v) if isinstance(v, (list, dict)) else v
    return out


def main():
    p = argparse.ArgumentParser()
    p.add_argument("src")
    p.add_argument("dst")
    p.add_argument("--max-candidates", type=int, default=50, help="skip rows with more candidates")
    p.add_argument("--limit", type=int, help="stop after this many rows")
    args = p.parse_args()
    kept = 0
    with open(args.src) as src, open(args.dst, "w") as dst:
        for line in src:
            row = json.loads(line)
            if len(row["candidates"]) - bool(row["anchor"]) > args.max_candidates:
                continue
            dst.write(json.dumps(to_grpo(row)) + "\n")
            kept += 1
            if kept == args.limit:
                break
    print(f"wrote {kept} rows to {args.dst}")


if __name__ == "__main__":
    main()
