"""Fixed vocabularies shared by the catalog tagger, profile generator, retrieval and reward.

Colors match the app's swatch names in src/theme/index.ts, so every tag has a swatch.
Changing a list here means re-tagging the catalog and regenerating training data.
"""

SLOTS = ("top", "bottom", "dress", "outerwear", "shoes", "accessory")
DEPARTMENTS = ("men", "women", "unisex")
SEASONS = ("spring", "summer", "fall", "winter")

# COLORS

COLORS = (
    # NEUTRALS
    "white", "cream", "beige", "tan", "khaki",
    "brown", "gray", "charcoal", "black",
    # VERSATILES
    "navy", "denim", "olive", "blue", "forest-green", "muted-green",
    "burgundy", "light-blue", "lilac", "gold", "silver",
    # ACCENTS
    "yellow", "orange", "red", "pink", "purple",
)

NEUTRALS = frozenset({
    "white", "cream", "beige", "tan", "khaki",
    "brown", "gray", "charcoal", "black",
})

VERSATILES = frozenset({
    "navy", "denim", "olive", "blue", "forest-green", "muted-green",
    "burgundy", "light-blue", "lilac", "gold", "silver",
})

ACCENTS = frozenset({
    "yellow", "orange", "red", "pink", "purple",
})

COLOR_COMPATIBILITY = {
    "neutral": {
        "neutral": 1.0,
        "versatile": 1.0,
        "accent": 0.9,
    },
    "versatile": {
        "neutral": 1.0,
        "versatile": 0.9,
        "accent": 0.75,
    },
    "accent": {
        "neutral": 0.9,
        "versatile": 0.75,
        "accent": 0.6,
    },
}

COLOR_GROUP = {
    **{c: "neutral" for c in NEUTRALS},
    **{c: "versatile" for c in VERSATILES},
    **{c: "accent" for c in ACCENTS},
}

# PATTERN / FIT

PATTERNS = ("solid", "stripe", "check", "small-print", "large-print", "graphic")
# More than one of these in an outfit competes for attention.
LOUD_PATTERNS = frozenset({"check", "large-print", "graphic"})

FITS = ("slim", "regular", "relaxed", "oversized")
# Shoes and accessories have no fit.
FIT_SLOTS = frozenset({"top", "bottom", "dress", "outerwear"})

# STYLE / OCCASION

STYLE_TAGS = (
    "minimal", "old-money", "western", "preppy",
    "streetwear", "techwear", "workwear", "outdoors", "athleisure",
    "bohemian", "y2k", "goth", "coastal", "sporty",
    "clean-girl", "soft-girl", "grunge"
)
MAX_STYLE_TAGS = 3

# Formality runs 1 to 5. Inclusive target range per occasion (PLAN section 5).
OCCASION_FORMALITY = {
    "formal": (4, 5),
    "semi-formal": (4, 5),
    "work": (3, 4),
    "everyday": (2, 4),
    "party": (2, 4),
    "casual": (1, 3),
    "athletic": (1, 2),
    "comfy": (1, 2),
}
