"""Hand-written outfits for the reward (PLAN.md section 6).

Run from the repo root: `python -m pytest training/test_reward.py` or `python -m training.test_reward`.
"""

import json

from training import reward as R
from training import vocab


ALL_YEAR = ["spring", "summer", "fall", "winter"]


def item(id, slot, price, colors, formality, tags, name, pattern="solid", fit=None, season=ALL_YEAR):
    return {"id": id, "slot": slot, "price": price, "colors": colors, "formality": formality,
            "style_tags": tags, "name": name, "pattern": pattern, "fit": fit, "season": season}


CANDIDATES = [
    item("top_001", "top", 40.0, ["cream"], 2, ["minimal"], "Relaxed cotton crewneck", fit="relaxed"),
    item("top_002", "top", 60.0, ["red"], 3, ["preppy"], "Silk camp shirt", fit="slim"),
    item("top_003", "top", 45.0, ["pink"], 2, ["bohemian"], "Floral blouse", "small-print", "relaxed"),
    item("bottom_001", "bottom", 70.0, ["denim"], 2, ["minimal", "workwear"], "Straight leg jeans",
         fit="regular"),
    item("bottom_002", "bottom", 90.0, ["black"], 4, ["old-money"], "Pleated wool trousers", fit="regular"),
    item("bottom_004", "bottom", 60.0, ["khaki"], 2, ["preppy"], "Straight cotton chinos", fit="regular"),
    item("bottom_003", "bottom", 50.0, ["orange"], 2, ["y2k"], "Satin mini skirt", "large-print", "slim"),
    item("dress_001", "dress", 120.0, ["muted-green"], 2, ["bohemian", "minimal"], "Linen midi dress",
         fit="relaxed", season=["spring", "summer"]),
    item("shoes_001", "shoes", 80.0, ["white"], 2, ["minimal"], "Leather court sneakers"),
    item("shoes_002", "shoes", 150.0, ["black"], 5, ["old-money"], "Patent derby shoes"),
    item("outerwear_001", "outerwear", 110.0, ["olive"], 2, ["workwear"], "Waxed chore jacket",
         fit="relaxed", season=["fall", "winter"]),
    item("accessory_001", "accessory", 25.0, ["orange"], 2, ["streetwear", "y2k"], "Canvas baseball cap",
         "graphic"),
    item("accessory_002", "accessory", 30.0, ["gray"], 2, ["minimal"], "Knit beanie"),
    item("accessory_003", "accessory", 20.0, ["black"], 2, ["minimal"], "Leather belt"),
    item("accessory_004", "accessory", 35.0, ["red"], 3, ["preppy"], "Silk scarf"),
    item("closet_3", "top", 0.0, ["navy"], 2, ["preppy", "minimal"], "navy oxford shirt", fit="regular"),
]


def ctx(**over):
    row = {
        "occasion": "everyday", "budget_min": 100.0, "budget_max": 250.0, "anchor": None,
        "candidates": CANDIDATES, "profile_style_tags": ["minimal", "workwear", "preppy"],
        "profile_fits": ["relaxed", "regular"], "profile_avoid": ["y2k"],
    }
    row.update(over)
    return row


def outfit(items, reason="The cream crewneck and jeans keep it easy with white sneakers."):
    return {"items": items, "reason": reason}


GOOD = outfit(["top_001", "bottom_001", "shoes_001"])


def score(o, **over):
    return R.score_outfit(o, ctx(**over))


def breakdown(ids, key, **over):
    return score(outfit(ids), **{"budget_max": 1000.0, **over})[2][key]


def text(*outfits, **extra):
    return json.dumps({"outfits": list(outfits), **extra})


def test_vocab_copy_matches():
    assert R.NEUTRALS == vocab.NEUTRALS
    assert R.VERSATILES == vocab.VERSATILES
    assert R.ACCENTS == vocab.ACCENTS
    assert R.COLOR_GROUP == vocab.COLOR_GROUP
    assert R.COLOR_COMPATIBILITY == vocab.COLOR_COMPATIBILITY
    assert R.STYLE_TAGS == vocab.STYLE_TAGS
    assert R.OCCASION_FORMALITY == vocab.OCCASION_FORMALITY
    assert R.LOUD_PATTERNS == vocab.LOUD_PATTERNS


def test_clearly_good_scores_max():
    s, ok, b = score(GOOD)
    assert ok and s == 7.5, b


def test_closet_anchor_free_and_counted_at_budget_min():
    o = outfit(["closet_3", "bottom_002", "shoes_001"],
               "The oxford shirt dresses up the trousers without trying too hard.")
    s, ok, b = score(o, anchor={"source": "closet", "id": "closet_3"}, budget_min=170.0)
    # Formality 2 and 4 are two levels apart, so only that check fails.
    assert ok and b["budget"] == 1.0 and b["anchor"] == 1.0 and b["formality"] == 0.0, b


def test_closet_price_in_column_is_ignored():
    cands = [dict(c, price=99.0) if c["id"] == "closet_3" else c for c in CANDIDATES]
    o = outfit(["closet_3", "bottom_001", "shoes_001"], "Your oxford shirt with jeans.")
    assert score(o, candidates=cands, anchor={"source": "closet", "id": "closet_3"})[2]["budget"] == 1.0


def test_catalog_anchor_missing_costs_one():
    s, ok, b = score(GOOD, anchor={"source": "catalog", "id": "outerwear_001"})
    assert ok and b["anchor"] == 0.0 and s == 6.5


def test_budget_is_a_gate_with_edges_included():
    assert score(GOOD, budget_min=190.0)[:2] == (7.5, True)
    assert score(GOOD, budget_max=190.0)[:2] == (7.5, True)
    assert score(GOOD, budget_max=189.99) == (0.0, False, {"outside_budget": 190.0})
    assert score(GOOD, budget_min=190.01) == (0.0, False, {"outside_budget": 190.0})


def test_a_stated_total_is_ignored():
    assert R.parse_output(text({**GOOD, "total": 5})) == [GOOD]
    assert R.parse_output(text({**GOOD, "total": "190"})) == [GOOD]
    assert score({**GOOD, "total": 5})[2]["budget"] == 1.0


def test_dress_without_bottom_is_complete():
    o = outfit(["dress_001", "shoes_001"], "The linen dress with white sneakers is easy and fresh.")
    s, ok, b = score(o)
    assert ok and b["complete"] == 1.0 and s == 7.5, b


def test_incomplete_outfits():
    assert score(outfit(["dress_001", "bottom_001", "shoes_001"]), budget_max=300.0)[2]["complete"] == 0.0
    assert score(outfit(["top_001", "bottom_001"]))[2]["complete"] == 0.0
    assert score(outfit(["top_001", "closet_3", "bottom_001", "shoes_001"]))[2]["complete"] == 0.0
    assert score(outfit(["top_001", "top_001", "bottom_001", "shoes_001"]))[2]["complete"] == 0.0


def test_two_accessories_and_outerwear_allowed():
    o = outfit(["top_001", "bottom_001", "shoes_001", "accessory_002", "accessory_003"])
    s, ok, b = score(o)
    assert ok and b["complete"] == 1.0 and s == 7.5, b


def test_invented_item_fails_gate():
    s, ok, b = score(outfit(["top_001", "bottom_999", "shoes_001"]))
    assert (s, ok) == (0.0, False) and b == {"invented": ["bottom_999"]}


def test_color_tiers():
    assert breakdown(["top_001", "bottom_002", "shoes_001"], "color") == 1.0
    assert breakdown(["top_002", "bottom_002", "shoes_001"], "color") == 0.9
    assert breakdown(["top_002", "bottom_003", "shoes_001"], "color") == 0.6
    assert breakdown(["top_002", "bottom_001", "shoes_001"], "color") == 0.75
    assert breakdown(["top_002", "bottom_002", "shoes_001", "accessory_004"], "color") == 0.9
    assert breakdown(["dress_001", "shoes_001"], "color") == 1.0


def test_pattern_rule():
    assert breakdown(["top_001", "bottom_003", "shoes_001", "accessory_001"], "pattern") == 0.0
    assert breakdown(["top_003", "bottom_003", "shoes_001"], "pattern") == 0.5
    no_pattern = [{k: v for k, v in c.items() if k != "pattern"} for c in CANDIDATES]
    assert breakdown(["top_001", "bottom_003", "shoes_001"], "pattern", candidates=no_pattern) == 0.5


def test_season_rule():
    assert breakdown(["dress_001", "outerwear_001", "shoes_001"], "season") == 0.0
    assert breakdown(["dress_001", "shoes_001"], "season") == 0.5
    unseasoned = [dict(c, season=[]) if c["id"] == "outerwear_001" else c for c in CANDIDATES]
    assert breakdown(["dress_001", "outerwear_001", "shoes_001"], "season", candidates=unseasoned) == 0.5
    seasonless = [{k: v for k, v in c.items() if k != "season"} for c in CANDIDATES]
    assert breakdown(["dress_001", "outerwear_001", "shoes_001"], "season", candidates=seasonless) == 0.5


def test_formality_rules():
    mixed = outfit(["top_001", "bottom_001", "shoes_002"], "Jeans and derby shoes.")
    assert score(mixed, budget_max=300.0)[2]["formality"] == 0.0
    assert score(GOOD, occasion="work")[2]["formality"] == 0.0
    assert score(GOOD, occasion="not_an_occasion")[2]["formality"] == 0.0


def test_profile_avoid_style_and_fit():
    with_cap = outfit(["top_001", "bottom_001", "shoes_001", "accessory_001"])
    assert score(with_cap)[2]["profile"] == 0.0
    # Crewneck misses on style only, jeans match both, sneakers have no fit and miss on style.
    assert score(GOOD, profile_style_tags=["workwear"], profile_fits=[])[2]["profile"] == 1 / 3
    assert score(GOOD, profile_style_tags=["workwear"])[2]["profile"] == (0.5 + 1 + 0) / 3
    # A fit mismatch halves an item that matches on style.
    assert score(GOOD, profile_fits=["regular"])[2]["profile"] == (0.5 + 1 + 1) / 3
    assert score(GOOD, profile_style_tags=[], profile_fits=[])[2]["profile"] == 1.0
    # A closet anchor the user chose is never held against them.
    o = outfit(["closet_3", "bottom_001", "shoes_001"], "Your oxford shirt with jeans.")
    assert score(o, anchor={"source": "closet", "id": "closet_3"}, profile_avoid=["navy"])[2]["profile"] == 1.0


def test_reason_rules():
    assert score({**GOOD, "reason": "Looks great. Very comfy."})[2]["reason"] == 0.0
    assert score({**GOOD, "reason": "A comfortable everyday look."})[2]["reason"] == 0.0
    assert score({**GOOD, "reason": "Pairs top_001 with denim."})[2]["reason"] == 0.5
    assert score({**GOOD, "reason": "The jean and sneaker combo is easy!"})[2]["reason"] == 0.5
    assert score({**GOOD, "reason": " ".join(["jeans"] * 41)})[2]["reason"] == 0.0
    # A period after an abbreviation or before a lowercase word doesn't end the sentence.
    assert score({**GOOD, "reason": "Dr. Martens would toughen up the cream crewneck."})[2]["reason"] == 0.5
    assert score({**GOOD, "reason": "The Jr. Varsity cut, e.g. this crewneck, sits easy."})[2]["reason"] == 0.5
    assert score({**GOOD, "reason": "Dr. Martens fans. Cream crewneck."})[2]["reason"] == 0.0
    shirt = [{**c, "name": "Buffalo Check Shirt | Hawk"} if c["id"] == "top_001" else c for c in CANDIDATES]
    assert score({**GOOD, "reason": "The buffalo check shirt keeps it easy."}, candidates=shirt)[2]["reason"] == 0.5


def test_parse_rejects_bad_shapes():
    assert R.parse_output(text(GOOD)) == [GOOD]
    assert R.parse_output(text(GOOD, note="hi")) is None
    assert R.parse_output(text({**GOOD, "extra": 1})) is None
    assert R.parse_output('{"outfits": [') is None
    assert R.parse_output("```json\n" + text(GOOD) + "\n```") is None
    assert R.parse_output(text(GOOD, GOOD, GOOD, GOOD)) is None
    assert R.parse_output(text()) is None
    assert R.parse_output(text({**GOOD, "items": []})) is None
    assert R.parse_output(text({"items": GOOD["items"]})) is None


def test_completion_mean_over_three_and_repeats():
    other = outfit(["dress_001", "shoes_001"], "The linen dress with white sneakers.")
    third = outfit(["closet_3", "bottom_004", "shoes_001"], "Your oxford shirt with chinos.")
    c = ctx()
    assert R.score_completion(text(GOOD, other, third), c) == 7.5
    assert R.score_completion(text(GOOD), c) == round(7.5 / 3, 4)
    assert R.score_completion(text(GOOD, GOOD, GOOD), c) == round(7.5 / 3, 4)
    assert R.score_completion("not json", c) == 0.0


def test_reward_entry_point_handles_messages_and_json_columns():
    good = text(GOOD)
    completions = [good, [{"role": "assistant", "content": good}], "oops"]
    row = ctx()
    kwargs = {k: [json.dumps(row[k])] * 3 for k in R.CONTEXT_COLUMNS}
    kwargs["occasion"] = ["everyday"] * 3
    kwargs["prompts"] = ["p"] * 3
    got = R.reward(completions, **kwargs)
    assert got == [round(7.5 / 3, 4)] * 2 + [0.0]


def test_ranking_and_spread():
    good2 = outfit(["dress_001", "shoes_001"], "The linen dress with white sneakers.")
    good3 = outfit(["closet_3", "bottom_004", "shoes_001"], "Your oxford shirt with chinos.")
    meh = outfit(["top_002", "bottom_001", "shoes_002", "outerwear_001"], "A bold red layered look.")
    bad = outfit(["top_002", "bottom_003", "shoes_002", "accessory_001"], "Great. Fun.")
    cases = {
        "three good": text(GOOD, good2, good3),
        "two good": text(GOOD, good2),
        "good + meh + bad": text(GOOD, meh, bad),
        # Returning fewer outfits than asked costs more than returning weaker ones.
        "meh + meh + bad": text(meh, outfit(["top_002", "bottom_002", "shoes_002"], "Sharp."), bad),
        "one good": text(GOOD),
        "all bad": text(bad),
        "invented": text(outfit(["top_001", "bottom_999", "shoes_001"])),
        "malformed": text(GOOD)[:-2],
    }
    scores = {k: R.score_completion(v, ctx(budget_max=400.0)) for k, v in cases.items()}
    for k, v in scores.items():
        print(f"{v:6.3f}  {k}")
    order = list(scores.values())
    assert order == sorted(order, reverse=True), scores
    assert len(set(order)) >= 6


if __name__ == "__main__":
    tests = [f for n, f in sorted(globals().items()) if n.startswith("test_")]
    for f in tests:
        f()
    print(f"{len(tests)} tests passed")
