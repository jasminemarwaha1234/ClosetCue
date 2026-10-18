from typing import Annotated, Literal, Optional, Union

from pydantic import BaseModel, Field, StringConstraints, model_validator

# The API contract between the app and the backend. src/api/types.ts mirrors this file.
# Every route except /health, /scan and /faces/find-owner needs the header
# `Authorization: Bearer <Supabase access token>` from the app's anonymous sign-in.
# Errors use FastAPI's default shape: a non-2xx status and {"detail": "..."}.


class Item(BaseModel):
    """One photo thumbnail. `id` is the phone's media-library asset id."""
    id: str
    base64: str


# POST /scan
class ScanRequest(BaseModel):
    items: list[Item]
    owner_embedding: Optional[list[float]] = None


# GET /catalog -> list[CatalogItem]
Slot = Literal["top", "bottom", "dress", "outerwear", "shoes", "accessory"]
Department = Literal["men", "women", "unisex"]


class CatalogItem(BaseModel):
    id: str
    name: str
    brand: str
    slot: Slot
    department: Department
    price: float
    colors: list[str]
    formality: int  # 1 athleisure ... 5 formal
    style_tags: list[str]
    season: list[str]
    image: str  # image URL
    url: str  # retailer page


# POST /profile (ProfileRequest) -> StyleProfile, built from photos and saved
# GET /profile -> StyleProfile, or 404 when the user has none yet
# PUT /profile (StyleProfile) -> StyleProfile, the user's edits
class ProfileRequest(BaseModel):
    photos: list[Item]


class Look(BaseModel):
    name: str
    # Asset ids, so the app can show the photos again without the server storing them.
    photo_ids: list[str]


ClosetId = Annotated[str, StringConstraints(pattern=r"^closet_\d+$")]


class ClosetItem(BaseModel):
    """A garment the user already owns, tagged by Gemini from one of their photos. Never bought."""
    id: ClosetId  # unique within the user's profile
    description: str  # "navy oxford shirt"
    slot: Slot
    colors: list[str]
    formality: int
    style_tags: list[str]
    photo_id: str  # asset id of the photo it came from, so the app can show it


class StyleProfile(BaseModel):
    summary: str
    style_tags: list[str]  # same vocabulary as CatalogItem.style_tags
    colors: list[str]  # colors the user wears most
    avoid: list[str]  # style tags or colors to leave out, such as "logos"
    departments: list[Literal["men", "women"]]  # catalog sections to show; unisex items always show
    looks: list[Look]
    closet: list[ClosetItem]


# POST /outfits (OutfitsRequest) -> OutfitsResponse
Occasion = Literal[
    "everyday", "work", "date", "party", "formal", "active",
    "wedding_guest", "interview", "brunch", "travel", "concert", "outdoors", "campus", "lounge",
]
GeneratedBy = Literal["our-llama", "base-llama", "gemini"]


class CatalogAnchor(BaseModel):
    source: Literal["catalog"]
    id: str  # a CatalogItem.id


class ClosetAnchor(BaseModel):
    source: Literal["closet"]
    id: ClosetId  # a ClosetItem.id from the user's profile


Anchor = Annotated[Union[CatalogAnchor, ClosetAnchor], Field(discriminator="source")]


# An anchor id missing from the catalog or the user's closet is a 422 from the route.
class OutfitsRequest(BaseModel):
    anchor: Optional[Anchor] = None  # None means "I need an outfit for..." with no anchor
    budget_min: float = Field(ge=0)
    budget_max: float = Field(gt=0)
    max_item_price: Optional[float] = Field(default=None, gt=0)  # no single catalog item may cost more
    occasion: Occasion
    # "Make it nicer": ids of the outfit's items and owned pieces. The backend returns one
    # pricier version with the budget range moved up to (that outfit's total, total + $150],
    # so it can exceed budget_max. The checkout mandate is what refuses it.
    upgrade_of: Optional[list[str]] = None

    @model_validator(mode="after")
    def _check_budget(self) -> "OutfitsRequest":
        if self.budget_min > self.budget_max:
            raise ValueError("budget_min is above budget_max")
        return self


class Outfit(BaseModel):
    id: str  # opaque; the backend doesn't store outfits
    items: list[CatalogItem]  # what would be bought, a catalog anchor included
    owned: list[ClosetItem]  # pieces from the user's closet; free and never in the cart
    total: float  # sum of `items` prices only, computed by the backend and rounded to cents
    reason: str
    # Item id -> up to 3 same-slot alternatives that keep the total within the budget range.
    # The anchor and owned pieces have none. The app swaps locally, re-adds the prices,
    # and keeps looking up swaps under the original id.
    swaps: dict[str, list[CatalogItem]]


# A 503 when every generator fails, never an empty list.
class OutfitsResponse(BaseModel):
    outfits: list[Outfit] = Field(min_length=1, max_length=3)
    generated_by: GeneratedBy  # covers every outfit; the app labels anything that isn't "our-llama"


# POST /tryon (TryOnRequest) -> TryOnResponse
class TryOnRequest(BaseModel):
    photo: Item  # a full-body photo of the user
    item_ids: list[str]


class TryOnResponse(BaseModel):
    image_base64: str  # JPEG


# POST /checkout/mandate (MandateRequest) -> Mandate
# POST /checkout/cart (CartRequest) -> CartAllowed | CartRefused, checked before Face ID
# POST /checkout/confirm (CartRequest) -> Receipt, or 409 if the cart no longer fits
class MandateRequest(BaseModel):
    limit: float  # the app defaults this to the request's budget_max
    hours: int = 24


class CardRef(BaseModel):
    label: str  # "Visa •••• 1234, agent card": the Stripe Issuing card's last 4. The agent never sees the card number.


class Mandate(BaseModel):
    id: str
    limit: float
    spent: float
    category: Literal["apparel"]
    expires_at: str  # ISO 8601
    card: CardRef


class CartRequest(BaseModel):
    mandate_id: str
    item_ids: list[str]


RefusalReason = Literal["over_limit", "expired", "not_apparel"]


# `total` is always computed by the backend from catalog prices, never taken from the app.
class CartAllowed(BaseModel):
    status: Literal["allowed"]
    total: float
    remaining: float  # mandate limit minus what's already spent


class CartRefused(BaseModel):
    status: Literal["refused"]
    total: float
    remaining: float
    reason: RefusalReason
    message: str  # shown to the user
    suggestion: Optional[Outfit] = None  # the closest outfit that fits


CartVerdict = Union[CartAllowed, CartRefused]


class Receipt(BaseModel):
    order_id: str
    items: list[CatalogItem]
    total: float
    remaining: float
    card: CardRef
    authorization_id: Optional[str] = None  # Stripe Issuing's iauth_...; None means a simulated payment
    created_at: str  # ISO 8601


# GET /rate/next -> RatePair
# POST /rate (RateChoice) -> 204
class RatePair(BaseModel):
    pair_id: str
    request: OutfitsRequest  # the request both outfits answer
    profile_summary: str
    a: Outfit
    b: Outfit  # only the backend knows which model made which


class RateChoice(BaseModel):
    pair_id: str
    choice: Literal["a", "b"]


# DELETE /me -> 204, after deleting the user's profile, feedback and mandates
