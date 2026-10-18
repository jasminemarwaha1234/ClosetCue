# GET /rate/next and POST /rate: the blind A/B test on the "Which is better?" screen (PLAN.md section 6, item 5).
#
# Pairs are built ahead of time from two models' eval answers by backend/build_rate_pairs.py, which also
# fixes which model is a and which is b. The app only ever sees the RatePair; a_model and b_model stay
# here and go into the feedback table with the user's choice.

import json
import random
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException

from backend.schemas import RateChoice, RatePair
from backend.services import supabase

router = APIRouter()

PAIRS = Path(__file__).resolve().parents[1] / "data" / "rate_pairs.jsonl"


def _pairs() -> dict[str, dict]:
    """{pair_id: {"pair": RatePair dict, "a_model", "b_model"}}, read on each call so a rebuild needs no restart."""
    if not PAIRS.exists():
        raise HTTPException(503, "There are no outfits to compare yet. Check back soon.")
    rows = [json.loads(line) for line in PAIRS.read_text().splitlines() if line.strip()]
    return {row["pair"]["pair_id"]: row for row in rows}


@router.get("/rate/next")
async def next_pair(user_id: str = Depends(supabase.current_user)) -> RatePair:
    pairs = _pairs()
    rated = await supabase.rated_pair_ids(user_id)
    left = [row for pair_id, row in pairs.items() if pair_id not in rated]
    if not left:
        raise HTTPException(404, "You've rated every pair. Thanks for helping!")
    return RatePair(**random.choice(left)["pair"])


@router.post("/rate", status_code=204)
async def rate(choice: RateChoice, user_id: str = Depends(supabase.current_user)) -> None:
    row = _pairs().get(choice.pair_id)
    if row is None:
        raise HTTPException(422, f"{choice.pair_id} isn't a pair we showed")
    await supabase.add_feedback(user_id, choice.pair_id, choice.choice, row["pair"], row["a_model"], row["b_model"])
