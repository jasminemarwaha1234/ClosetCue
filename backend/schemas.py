from typing import Literal, Optional, Union

from pydantic import BaseModel

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


class CatalogItem(BaseModel):
    id: str
    name: str
    brand: str
    slot: Slot
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


class StyleProfile(BaseModel):
    summary: str
    style_tags: list[str]  # same vocabulary as CatalogItem.style_tags
    colors: list[str]  # colors the user wears most
    formality: int  # 1-5, what they usually wear
    avoid: list[str]  # style tags or colors to leave out, such as "logos"
    looks: list[Look]


# POST /outfits (OutfitsRequest) -> OutfitsResponse
Occasion = Literal["everyday", "work", "date", "party", "formal", "active"]
GeneratedBy = Literal["our-llama", "base-llama", "gemini"]


class OutfitsRequest(BaseModel):
    anchor_id: Optional[str] = None  # None means "I need an outfit for..." with no anchor
    budget: float
    occasion: Occasion


class Outfit(BaseModel):
    id: str
    items: list[CatalogItem]
    total: float
    reason: str
    # Item id -> up to 3 same-slot alternatives that keep the total within budget.
    # The anchor has none. The app swaps locally and re-adds the prices.
    swaps: dict[str, list[CatalogItem]]


class OutfitsResponse(BaseModel):
    outfits: list[Outfit]
    generated_by: GeneratedBy  # the app labels anything that isn't "our-llama"


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
    limit: float
    hours: int = 24


class CardRef(BaseModel):
    label: str  # "Visa •••• 4242, agent token". The agent never sees the card number.


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


# POST /fit (FitFeedback) -> StyleProfile, updated from the ratings
FitRating = Literal["too_small", "right", "too_big"]


class ItemFit(BaseModel):
    item_id: str
    fit: FitRating
    liked: bool


class FitFeedback(BaseModel):
    order_id: str
    items: list[ItemFit]


# DELETE /me -> 204, after deleting the user's profile, feedback and mandates
