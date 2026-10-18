"""Fixed vocabularies shared by the catalog tagger, profile generator, retrieval and reward.

Colors match the app's swatch names in src/theme/index.ts, so every tag has a swatch.
Changing a list here means re-tagging the catalog and regenerating training data.
"""

SLOTS = ("top", "bottom", "dress", "outerwear", "shoes", "accessory")
DEPARTMENTS = ("men", "women", "unisex")
SEASONS = ("spring", "summer", "fall", "winter")

COLORS = (
    "white", "cream", "beige", "tan", "khaki", "brown",
    "gray", "charcoal", "black", "navy", "denim",
    "blue", "green", "olive", "yellow", "orange", "red", "burgundy", "pink", "lilac", "purple",
    "gold", "silver",
)
# Go with anything. An outfit may add at most one color outside this set (PLAN section 5 reward).
NEUTRALS = frozenset({
    "white", "cream", "beige", "tan", "khaki", "brown",
    "gray", "charcoal", "black", "navy", "denim", "gold", "silver",
})
# Accent pairs that clash in one outfit.
CLASHES = frozenset(frozenset(p) for p in [
    ("red", "pink"), ("red", "orange"), ("red", "purple"), ("orange", "pink"),
    ("orange", "purple"), ("green", "red"), ("yellow", "purple"), ("burgundy", "orange"),
])

STYLE_TAGS = (
    "minimal", "classic", "relaxed", "tailored", "smart-casual", "preppy",
    "streetwear", "graphic", "workwear", "outdoors", "athleisure",
    "vintage", "bohemian", "romantic", "edgy", "trendy", "logos",
)

# Formality runs 1 (athleisure) to 5 (formal). Inclusive target range per occasion (PLAN section 5).
OCCASION_FORMALITY = {
    "everyday": (1, 3),
    "work": (3, 4),
    "date": (2, 4),
    "party": (2, 4),
    "formal": (5, 5),
    "active": (1, 1),
    "wedding_guest": (4, 5),
    "interview": (4, 5),
    "brunch": (2, 3),
    "travel": (1, 2),
    "concert": (1, 3),
    "outdoors": (1, 2),
    "campus": (1, 2),
    "lounge": (1, 1),
}
