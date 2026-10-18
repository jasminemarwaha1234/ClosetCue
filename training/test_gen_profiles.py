"""Run with `python -m pytest training/test_gen_profiles.py`."""

import json
import re

import pytest

from training import reward
from training.gen_profiles import generate, main
from training.vocab import (
    COLOR_COMPATIBILITY, COLOR_GROUP, COLORS, FIT_SLOTS, FITS, MAX_STYLE_TAGS, OCCASION_FORMALITY,
    PATTERNS, SEASONS, SLOTS, STYLE_TAGS,
)

PROFILES = generate(60, seed=0)
CLOSETS = [(p, item) for p in PROFILES for item in p["closet"]]


def test_deterministic_and_prefix_stable():
    assert generate(60, seed=0) == PROFILES
    assert generate(5, seed=0) == PROFILES[:5]
    assert generate(5, seed=1) != PROFILES[:5]


def test_cli_writes_jsonl(tmp_path, monkeypatch):
    out = tmp_path / "data" / "profiles.jsonl"
    monkeypatch.setattr("sys.argv", ["gen_profiles", "--n", "3", "--seed", "0", "--out", str(out)])
    main()
    assert [json.loads(line) for line in out.read_text().splitlines()] == PROFILES[:3]


def test_profile_fields_come_from_vocab():
    for p in PROFILES:
        assert p["id"] == f"profile_{PROFILES.index(p):04d}"
        assert "formality" not in p
        assert 1 <= len(p["style_tags"]) <= MAX_STYLE_TAGS and set(p["style_tags"]) <= set(STYLE_TAGS)
        assert 3 <= len(p["colors"]) <= 4 and set(p["colors"]) <= set(COLORS)
        assert p["fits"] and set(p["fits"]) <= set(FITS)
        assert p["avoid"] and set(p["avoid"]) <= set(STYLE_TAGS) | set(COLORS)
        assert p["departments"] in (["men"], ["women"], ["men", "women"])
        assert len(p["occasions"]) >= 2 and set(p["occasions"]) <= set(OCCASION_FORMALITY)
        assert p["looks"] == [] and p["summary"].endswith(".")


def test_budgets_in_range():
    for p in PROFILES:
        assert 0 <= p["budget_min"] <= 150
        assert 60 <= p["budget_max"] <= 400
        assert p["budget_min"] < p["budget_max"]


def test_colors_are_pairwise_compatible():
    for p in PROFILES:
        groups = [COLOR_GROUP[c] for c in p["colors"]]
        assert all(COLOR_COMPATIBILITY[a][b] >= 0.75 for i, a in enumerate(groups) for b in groups[i + 1:])
        assert groups.count("accent") <= 1


def test_avoid_contradicts_nothing_the_person_wears():
    for p, item in CLOSETS:
        assert not set(p["avoid"]) & set(p["style_tags"] + p["colors"])
        assert not set(p["avoid"]) & set(item["style_tags"] + item["colors"])


def test_closet_items_have_contract_ids_and_vocab_values():
    for p in PROFILES:
        closet = p["closet"]
        assert [item["id"] for item in closet] == [f"closet_{n}" for n in range(1, len(closet) + 1)]
        wears_dresses = "women" in p["departments"]
        assert len(closet) == (30 if wears_dresses else 25)
        assert any(item["slot"] == "dress" for item in closet) == wears_dresses
    for p, item in CLOSETS:
        assert re.fullmatch(r"closet_\d+", item["id"])
        assert item["slot"] in SLOTS and item["price"] == 0
        assert item["colors"] and set(item["colors"]) <= set(COLORS)
        assert 1 <= item["formality"] <= 5
        assert item["style_tags"] and set(item["style_tags"]) <= set(p["style_tags"])
        assert item["pattern"] in PATTERNS
        assert item["season"] and set(item["season"]) <= set(SEASONS)
        assert (item["fit"] in FITS) if item["slot"] in FIT_SLOTS else item["fit"] is None


def test_closet_names_are_distinct_and_matchable_by_the_reward():
    for p in PROFILES:
        names = [item["name"] for item in p["closet"]]
        assert len(set(names)) == len(names)
    for _, item in CLOSETS:
        assert reward._name_words(item), item["name"]


def test_closet_works_as_reward_candidates():
    p = PROFILES[0]
    by_slot = {}
    for item in p["closet"]:
        by_slot.setdefault(item["slot"], item)
    outfit_items = [by_slot["top"], by_slot["bottom"], by_slot["shoes"]]
    ctx = {
        "occasion": p["occasions"][0], "budget_min": 0, "budget_max": p["budget_max"],
        "anchor": {"source": "closet", "id": outfit_items[0]["id"]}, "candidates": p["closet"],
        "profile_style_tags": p["style_tags"], "profile_fits": p["fits"], "profile_avoid": p["avoid"],
    }
    outfit = {"items": [i["id"] for i in outfit_items], "total": 0, "reason": "x"}
    _, gates_passed, breakdown = reward.score_outfit(outfit, ctx)
    assert gates_passed and breakdown["complete"] == 1.0 and breakdown["budget"] == 1.0


def test_profiles_validate_as_style_profiles():
    schemas = pytest.importorskip("backend.schemas")
    for p in PROFILES:
        schemas.StyleProfile.model_validate(p)
