"""Run with `python -m pytest training/test_build_prompts.py`."""

import json
import random

from training import reward
from training.build_prompts import (
    ANCHOR_MIX, SIZES, _in_proportion, best_outfits, build_rows, complete_possible, main, split_profiles,
)
from training.gen_profiles import generate
from training.prompt import SYSTEM
from training.retrieval import format_candidates
from training.test_retrieval import make_catalog

PROFILES = generate(40, seed=0)
CATALOG = make_catalog()
ROWS = build_rows(PROFILES, CATALOG, per_profile=5, seed=0)


def test_deterministic():
    assert build_rows(PROFILES, CATALOG, per_profile=5, seed=0) == ROWS
    assert build_rows(PROFILES, CATALOG, per_profile=5, seed=1) != ROWS
    assert split_profiles(PROFILES, 0.25, seed=0) == split_profiles(PROFILES, 0.25, seed=0)


def test_split_by_profile_is_disjoint():
    train, held_out = split_profiles(generate(400, seed=0), 0.25, seed=0)
    assert (len(train), len(held_out)) == (300, 100)
    assert not {p["id"] for p in train} & {p["id"] for p in held_out}

    train, held_out = split_profiles(PROFILES[:20], 0.25, seed=0)
    assert (len(train), len(held_out)) == (15, 5)


def test_cli_files_share_no_profile(tmp_path, monkeypatch):
    profiles, catalog = tmp_path / "profiles.jsonl", tmp_path / "catalog.json"
    profiles.write_text("".join(json.dumps(p) + "\n" for p in PROFILES[:20]))
    catalog.write_text(json.dumps(CATALOG))
    monkeypatch.setattr("sys.argv", ["build_prompts", "--profiles", str(profiles), "--catalog", str(catalog),
                                     "--out-dir", str(tmp_path)])
    main()
    train = [json.loads(line) for line in (tmp_path / "prompts_train.jsonl").read_text().splitlines()]
    held_out = [json.loads(line) for line in (tmp_path / "prompts_eval.jsonl").read_text().splitlines()]
    assert (len(train), len(held_out)) == (30, 10)
    assert len({r["profile_id"] for r in train}) == 15 and len({r["profile_id"] for r in held_out}) == 5
    assert len({r["profile_id"] for r in held_out[:5]}) == 5
    assert not {r["profile_id"] for r in train} & {r["profile_id"] for r in held_out}


def test_anchor_mix():
    sources = [r["anchor"]["source"] if r["anchor"] else "none" for r in ROWS]
    # 200 rows: 90 catalog / 70 closet / 40 none, unless a profile had no anchor to offer.
    assert 85 <= sources.count("catalog") <= 90
    assert 65 <= sources.count("closet") <= 70
    assert 40 <= sources.count("none") <= 50


def test_candidate_sizes():
    # Retrieval returns fewer than asked when filters and the diversity cap leave too few, which
    # this small synthetic catalog does at 75 and 100, and now and then at 50; 25 always fills.
    rows = build_rows(PROFILES, make_catalog(400), per_profile=5, seed=0)
    sizes = [len(r["candidates"]) - (1 if r["anchor"] else 0) for r in rows]
    assert (sizes.count(25), max(sizes)) == (50, 100) and sizes.count(50) >= 45
    assert sorted(_in_proportion({s: 1 for s in SIZES}, 10, random.Random(0))) == [25, 25, 25, 50, 50, 50, 75, 75, 100, 100]
    assert sorted(_in_proportion(ANCHOR_MIX, 40, random.Random(0))) == ["catalog"] * 18 + ["closet"] * 14 + ["none"] * 8


def test_row_format_and_context():
    profiles = {p["id"]: p for p in PROFILES}
    for r in ROWS:
        assert list(r) == ["messages", *reward.CONTEXT_COLUMNS, "profile_id"]
        assert [m["role"] for m in r["messages"]] == ["system", "user"]
        assert r["messages"][0]["content"] == SYSTEM
        p = profiles[r["profile_id"]]
        assert r["occasion"] in p["occasions"]
        assert (r["budget_min"], r["budget_max"]) == (p["budget_min"], p["budget_max"])
        assert r["profile_style_tags"] == p["style_tags"] and r["profile_avoid"] == p["avoid"]
        ctx = reward.prepare_context(json.loads(json.dumps(r)))
        assert set(ctx["by_id"]) == {c["id"] for c in r["candidates"]}


def test_anchor_is_rendered():
    for r in ROWS:
        user = r["messages"][1]["content"]
        if r["anchor"] is None:
            assert "\nAnchor: none.\n" in user
            continue
        anchor = next(c for c in r["candidates"] if c["id"] == r["anchor"]["id"])
        assert f"must include:\n{format_candidates([anchor])}\n" in user
        assert r["anchor"]["source"] == ("closet" if anchor["id"].startswith("closet_") else "catalog")
        for c in r["candidates"]:
            if c is not anchor:
                assert f"\n{format_candidates([c])}\n" in user


def test_known_good_answer_scores_high():
    rows = [r for r in ROWS if complete_possible(r)]
    assert len(rows) >= 150
    for r in rows[:10]:
        ctx = reward.prepare_context(r)
        answer = json.dumps({"outfits": best_outfits(ctx)})
        assert reward.score_completion(answer, ctx) >= 5.5



def test_best_outfits_adds_an_accessory_to_reach_budget_min():
    def item(id, price):
        return {"id": id, "slot": id.split("_")[0], "price": price, "colors": ["black"], "formality": 2,
                "style_tags": ["minimal"]}
    row = {"occasion": "casual", "budget_min": 150, "budget_max": 200, "anchor": None,
           "candidates": [item("top_1", 30), item("top_2", 40), item("bottom_1", 50), item("shoes_1", 60),
                          item("accessory_1", 20)],
           "profile_style_tags": ["minimal"], "profile_fits": [], "profile_avoid": []}
    best = best_outfits(reward.prepare_context(row))
    assert [(o["items"], sum(price for i in o["items"] for c in row["candidates"] if c["id"] == i
                             for price in [c["price"]])) for o in best] == [
        (["top_2", "bottom_1", "shoes_1"], 150),
        (["top_1", "bottom_1", "shoes_1", "accessory_1"], 160),
        (["top_2", "bottom_1", "shoes_1", "accessory_1"], 170),
    ]
    assert reward.score_completion(json.dumps({"outfits": best}), row) == 7.5
    # With top_1 as the anchor, only outfits around it count.
    anchored = {**row, "anchor": {"source": "catalog", "id": "top_1"}}
    best = best_outfits(reward.prepare_context(anchored))
    assert [o["items"] for o in best] == [["top_1", "bottom_1", "shoes_1", "accessory_1"], ["top_1", "bottom_1", "shoes_1"]]
