"""Build the DPO dataset for v3-dpo from "try again with Gemini" presses.

Run from the repo root, with SUPABASE_URL and SUPABASE_SECRET_KEY in backend/.env:
    python -m training.build_dpo [--out training/data/dpo_train.jsonl] [--model our-llama]

Each press saved one row in Supabase's preferences table (backend/routes/outfits.py): the prompt
the models were asked with, Gemini's outfits as chosen and the outfits the user turned down as
rejected, both exactly the JSON the model emits. Only rows whose rejected outfits came from
--model are kept, so by default DPO trains on our model's own mistakes.

Each output row is {"prompt": [system, user], "chosen": [assistant], "rejected": [assistant]}, Veri's
conversational preference format: with a message-list prompt, its DPO docs want both answers as
message lists too.
"""

import argparse
import asyncio
import json
from pathlib import Path

from backend.services import supabase

HERE = Path(__file__).parent


def _assistant(content: str) -> list[dict]:
    return [{"role": "assistant", "content": content}]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=HERE / "data" / "dpo_train.jsonl")
    parser.add_argument("--model", choices=["our-llama", "base-llama"], default="our-llama",
                        help="keep rows that turned down this model's outfits")
    args = parser.parse_args()

    preferences = asyncio.run(supabase.list_preferences())
    rows = [{"prompt": p["prompt"], "chosen": _assistant(p["chosen"]), "rejected": _assistant(p["rejected"])}
            for p in preferences if p["rejected_model"] == args.model]
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows))
    print(f"wrote {len(rows)} of {len(preferences)} preference rows to {args.out}; "
          f"{len(preferences) - len(rows)} turned down another model")


if __name__ == "__main__":
    main()
