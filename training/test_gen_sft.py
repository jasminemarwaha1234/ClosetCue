"""Run with `python -m pytest training/test_gen_sft.py`."""

import json
import random

from training import reward
from training.build_prompts import best_outfits
from training.gen_sft import answer, main


def item(id, slot, price, name, colors=("black",), formality=2, tags=("minimal",)):
    return {"id": id, "slot": slot, "price": price, "colors": list(colors), "formality": formality,
            "style_tags": list(tags), "name": name, "pattern": "solid", "fit": None, "season": None}


ROW = {
    "messages": [{"role": "system", "content": "s"}, {"role": "user", "content": "u"}],
    "occasion": "casual", "budget_min": 50, "budget_max": 250,
    "anchor": {"source": "closet", "id": "closet_2"},
    "candidates": [
        item("top_001", "top", 40.1, "MERINO ROLL NECK SWEATER - BROWN"),
        item("top_002", "top", 55.25, "Tee - Black"),
        item("shoes_001", "shoes", 80.0, "The Damon Penny Loafer - Tobacco"),
        item("shoes_002", "shoes", 64.99, "Canvas Cruiser Slip On | White"),
        item("accessory_001", "accessory", 19.95, "Leather Belt"),
        item("closet_2", "bottom", 0.0, "black cargo pants"),
    ],
    "profile_style_tags": ["minimal", "coastal"], "profile_fits": [], "profile_avoid": [],
    "profile_id": "profile_0001",
}


def test_answer_is_the_best_outfits_in_the_prompt_format():
    text, why = answer(ROW, random.Random(0))
    assert why == "ok"
    assert text == json.dumps(json.loads(text), separators=(",", ":"), ensure_ascii=False)
    outfits = reward.parse_output(text)
    assert outfits is not None and len(outfits) == 3
    ctx = reward.prepare_context(ROW)
    best = best_outfits(ctx)
    assert [o["items"] for o in outfits] == [o["items"] for o in best]
    for o in outfits:
        assert list(o) == ["items", "reason"]
        assert "closet_2" in o["items"]
        assert reward._reason(o["reason"], o["items"], [ctx["by_id"][i] for i in o["items"]]) == 0.5
        assert "\n" not in o["reason"] and len(o["reason"].split()) <= reward.MAX_REASON_WORDS
    assert reward.score_completion(text, ctx) == reward.score_completion(json.dumps({"outfits": best}), ctx) == 7.5


def test_names_are_cleaned():
    text, _ = answer(ROW, random.Random(0))
    reasons = " ".join(o["reason"] for o in json.loads(text)["outfits"])
    assert "your black cargo pants" in reasons.lower()
    assert "MERINO" not in reasons and "- Brown" not in reasons and "the The" not in reasons
    assert "Tee - Black" not in reasons  # the color was no name word for the reward either


def test_deterministic():
    assert answer(ROW, random.Random(0)) == answer(ROW, random.Random(0))
    reasons = {tuple(o["reason"] for o in json.loads(answer(ROW, random.Random(s))[0])["outfits"]) for s in range(5)}
    assert len(reasons) > 1


def test_skips_a_row_whose_best_outfits_break_the_budget():
    assert answer({**ROW, "budget_max": 100}, random.Random(0)) == (None, "a top-3 outfit breaks a stated rule")


def test_cli_writes_chat_rows_and_skips_large_rows(tmp_path, monkeypatch):
    data, out = tmp_path / "prompts.jsonl", tmp_path / "sft.jsonl"
    data.write_text(json.dumps(ROW) + "\n")
    for limit, rows in ((50, 1), (4, 0)):
        monkeypatch.setattr("sys.argv", ["gen_sft", "--data", str(data), "--out", str(out),
                                         "--max-candidates", str(limit)])
        main()
        written = [json.loads(line) for line in out.read_text().splitlines()]
        assert len(written) == rows
    monkeypatch.setattr("sys.argv", ["gen_sft", "--data", str(data), "--out", str(out)])
    main()
    (row,) = [json.loads(line) for line in out.read_text().splitlines()]
    assert list(row) == ["messages"]
    assert [m["role"] for m in row["messages"]] == ["system", "user", "assistant"]
    assert row["messages"][2]["content"] == answer(ROW, random.Random("0-0"))[0]
