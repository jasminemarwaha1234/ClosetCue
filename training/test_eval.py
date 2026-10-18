"""training/eval.py with the model stubbed. Run with `python -m pytest training/test_eval.py`."""

import asyncio
import json
from pathlib import Path

import httpx
import pytest
from google.genai import errors

from training import eval as E
from training.prompt import render_prompt
from training.retrieval import retrieve

ROOT = Path(__file__).resolve().parent


def make_row(profile: dict, catalog: list[dict], *, occasion: str, anchor: dict | None, n: int = 25) -> dict:
    """A prompt row shaped like build_prompts.py's: messages plus the reward's context columns."""
    candidates = retrieve(
        catalog, profile, anchor=anchor, budget_max=profile["budget_max"], max_item_price=None, occasion=occasion, n=n,
    )
    return {
        "messages": render_prompt(
            profile, occasion=occasion, budget_min=profile["budget_min"], budget_max=profile["budget_max"],
            anchor=anchor, candidates=candidates,
        ),
        "occasion": occasion,
        "budget_min": profile["budget_min"],
        "budget_max": profile["budget_max"],
        "anchor": {"source": "closet" if anchor["id"].startswith("closet_") else "catalog", "id": anchor["id"]}
        if anchor else None,
        "candidates": candidates + ([anchor] if anchor else []),
        "profile_style_tags": profile["style_tags"],
        "profile_fits": profile["fits"],
        "profile_avoid": profile["avoid"],
        "profile_id": profile["id"],
    }


def real_rows() -> list[dict]:
    """Two rows from the generated profiles and the current catalog: a closet anchor, then none."""
    profiles = [json.loads(line) for line in (ROOT / "data" / "profiles.jsonl").read_text().splitlines()]
    catalog = json.loads((ROOT / "catalog.json").read_text())
    first, second = profiles[0], profiles[1]
    return [
        make_row(first, catalog, occasion=first["occasions"][0], anchor=first["closet"][0]),
        make_row(second, catalog, occasion=second["occasions"][0], anchor=None),
    ]


def item(id, price, color, name):
    return {"id": id, "slot": id.split("_")[0], "price": price, "colors": [color], "formality": 2,
            "style_tags": ["minimal"], "name": name}


# Every outfit from these scores the full 7.5 unless it breaks the budget ($50 to $150).
ROW = {
    "messages": [{"role": "system", "content": "s"}, {"role": "user", "content": "u"}],
    "occasion": "casual",
    "budget_min": 50,
    "budget_max": 150,
    "anchor": None,
    "candidates": [
        item("top_1", 30, "white", "Boxy Cotton Shirt"),
        item("top_2", 40, "gray", "Merino Sweater"),
        item("bottom_1", 50, "black", "Wide Trousers"),
        item("shoes_1", 60, "black", "Leather Loafers"),
        item("shoes_2", 100, "white", "Canvas Sneakers"),
    ],
    "profile_style_tags": ["minimal"],
    "profile_fits": [],
    "profile_avoid": [],
    "profile_id": "profile_test",
}


def outfit(ids, total):
    return {"items": ids, "total": total, "reason": "The cotton shirt and merino sweater keep it calm."}


def answer(*outfits):
    return json.dumps({"outfits": list(outfits)})


VALID = answer(outfit(["top_1", "bottom_1", "shoes_1"], 140), outfit(["top_2", "bottom_1", "shoes_1"], 150))
INVENTED = answer(outfit(["top_1", "bottom_9", "shoes_1"], 140))
OVER_BUDGET = answer(outfit(["top_1", "bottom_1", "shoes_2"], 180))
FENCED = f"```json\n{VALID}\n```"
GARBAGE = "Sure! Here are three outfits you'll love."


def stub(answers, monkeypatch):
    """Point every model at a stub that returns (or raises) the next of answers."""
    queue = list(answers)

    async def ask(messages):
        a = queue.pop(0)
        if isinstance(a, Exception):
            raise a
        return a

    monkeypatch.setattr(E, "MODELS", {"gemini": ask})
    monkeypatch.setattr(E, "DELAY", 0)


def test_metrics_on_fake_answers(monkeypatch, tmp_path):
    stub([VALID, INVENTED, OVER_BUDGET, FENCED, GARBAGE], monkeypatch)
    records, stopped = asyncio.run(E.run("gemini", [ROW] * 5, tmp_path / "gemini.jsonl"))

    assert stopped is None
    assert [r["reward"] for r in records] == [5.0, 0.0, 2.1667, 0.0, 0.0]
    assert [r["live_kept"] for r in records] == [2, 0, 0, 2, 0]
    assert [r["fenced"] for r in records] == [False, False, False, True, False]
    # The best answer pairs the two in-budget outfits (7.5 each) with one over budget (6.5).
    assert [r["best_possible"] for r in records] == [7.1667] * 5
    s = E.summarize(records, "gemini", stopped)
    assert {k: v for k, v in s.items() if not k.startswith("latency")} == {
        "model": "gemini",
        "answers": 5,
        "errors": 0,
        "stopped": None,
        "valid_json_pct": 60.0,
        "fenced": 1,
        "invented_pct": 20.0,
        "valid_no_invented_pct": 40.0,
        "outfits": 4,
        "complete_pct": 75.0,
        "within_budget_pct": 50.0,
        "anchor_pct": 75.0,
        "mean_reward": 1.433,
        "mean_reward_of_max_pct": 19.1,
        "mean_best_possible": 7.167,
        "mean_reward_of_best_pct": 20.0,
        "live_outfits_pct": 26.7,
        "live_answers_ok_pct": 40.0,
    }
    saved = [json.loads(line) for line in (tmp_path / "gemini.jsonl").read_text().splitlines()]
    assert [r["raw"] for r in saved] == [VALID, INVENTED, OVER_BUDGET, FENCED, GARBAGE]


def test_other_errors_are_recorded_and_the_run_goes_on(monkeypatch, tmp_path):
    stub([TimeoutError(), VALID], monkeypatch)
    records, stopped = asyncio.run(E.run("gemini", [ROW] * 2, tmp_path / "gemini.jsonl"))

    assert stopped is None
    assert [r["error"] for r in records] == ["TimeoutError()", None]
    s = E.summarize(records, "gemini", stopped)
    assert (s["answers"], s["errors"], s["mean_reward"]) == (1, 1, 5.0)


@pytest.mark.parametrize("quota", [
    errors.ClientError(429, {"error": {"message": "RESOURCE_EXHAUSTED"}}),
    httpx.HTTPStatusError("429", request=httpx.Request("POST", "http://x"), response=httpx.Response(429)),
])
def test_quota_stops_the_run_and_keeps_what_finished(quota, monkeypatch, tmp_path):
    stub([VALID, GARBAGE, quota, VALID], monkeypatch)
    records, stopped = asyncio.run(E.run("gemini", [ROW] * 4, tmp_path / "gemini.jsonl"))

    assert stopped.startswith("quota exhausted at row 2")
    assert len((tmp_path / "gemini.jsonl").read_text().splitlines()) == 2
    s = E.summarize(records, "gemini", stopped)
    assert (s["answers"], s["errors"], s["valid_json_pct"], s["mean_reward"]) == (2, 0, 50.0, 2.5)
    assert "Stopped early: quota exhausted" in E.report(s, records)


def test_unconfigured_model_stops_before_scoring(monkeypatch, tmp_path):
    stub([None], monkeypatch)
    records, stopped = asyncio.run(E.run("gemini", [ROW], tmp_path / "gemini.jsonl"))
    assert (records, stopped) == ([], "gemini isn't configured in backend/.env")


def test_cli_on_rows_built_from_real_profiles(monkeypatch, tmp_path, capsys):
    rows = real_rows()
    data = tmp_path / "eval.jsonl"
    data.write_text("".join(json.dumps(r) + "\n" for r in rows))

    def first(row, slot):
        return next(c["id"] for c in row["candidates"] if c["slot"] == slot)

    # An answer that only uses the row's own ids, with the anchor where there is one.
    answers = []
    for row in rows:
        ids = [first(row, slot) for slot in ("top", "bottom", "shoes")]
        if row["anchor"]:
            ids[0] = row["anchor"]["id"]
        answers.append(answer(outfit(ids, 0)))
    stub(answers, monkeypatch)
    monkeypatch.setattr("sys.argv", ["eval", "--model", "gemini", "--data", str(data), "--out", str(tmp_path / "out")])
    E.main()

    s = json.loads((tmp_path / "out" / "gemini_summary.json").read_text())
    assert (s["answers"], s["valid_json_pct"], s["invented_pct"], s["anchor_pct"]) == (2, 100.0, 0.0, 100.0)
    assert "Lowest reward" in capsys.readouterr().out
