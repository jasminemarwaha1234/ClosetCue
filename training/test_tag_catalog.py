"""Run with `python -m pytest training/test_tag_catalog.py`. Skipped without google-genai."""

import pytest

pytest.importorskip("google.genai")
from training.tag_catalog import PROMPT, validate  # noqa: E402

TOP = {"slot": "top", "department_hint": None}
SHOES = {"slot": "shoes", "department_hint": "women"}
TAGS = {"department": "men", "colors": ["navy", "navy"], "formality": 2,
        "style_tags": ["minimal"], "season": ["winter", "fall"], "pattern": "stripe", "fit": "relaxed"}


def test_valid_tags_are_cleaned():
    assert validate(TOP, TAGS) == {
        "department": "men", "colors": ["navy"], "formality": 2, "style_tags": ["minimal"],
        "season": ["fall", "winter"], "pattern": "stripe", "fit": "relaxed",
    }
    assert validate(SHOES, {**TAGS, "fit": None})["department"] == "women"


@pytest.mark.parametrize("item, change", [
    (TOP, {"fit": None}),
    (TOP, {"fit": "baggy"}),
    (SHOES, {"fit": "slim"}),
    (TOP, {"pattern": None}),
    (TOP, {"pattern": "plaid"}),
    (TOP, {"style_tags": ["minimal", "preppy", "y2k", "goth"]}),
    (TOP, {"style_tags": ["logos"]}),
    (TOP, {"colors": ["green"]}),
])
def test_invalid_tags_are_rejected(item, change):
    with pytest.raises(ValueError):
        validate(item, {**TAGS, **change})


def test_old_cache_entry_without_pattern_is_rejected():
    old = {k: v for k, v in TAGS.items() if k not in ("pattern", "fit")}
    with pytest.raises(ValueError):
        validate(TOP, old)


def test_prompt_lists_the_new_fields():
    assert "pattern: one of ['solid', 'stripe'" in PROMPT
    assert "1 to 3 from ['minimal'" in PROMPT
