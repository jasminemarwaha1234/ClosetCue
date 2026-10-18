// The API contract between the app and the backend. Mirrors backend/schemas.py.
// Every route except /health, /scan and /faces/find-owner needs the header
// `Authorization: Bearer <Supabase access token>` from the app's anonymous sign-in.
// Errors use FastAPI's default shape: a non-2xx status and { detail: string }.

// POST /scan, POST /faces/find-owner
export type Framing = 'full' | 'upper' | 'none';
export type ScanResult = { id: string; has_outfit: boolean; framing?: Framing; confidence?: number };
export type Candidate = { embedding: number[]; crop: string; photos: number };

// One photo thumbnail. `id` is the phone's media-library asset id.
export type Item = { id: string; base64: string };

// GET /catalog -> CatalogItem[]
export type Slot = 'top' | 'bottom' | 'dress' | 'outerwear' | 'shoes' | 'accessory';
export type Department = 'men' | 'women' | 'unisex';

export type CatalogItem = {
  id: string;
  name: string;
  brand: string;
  slot: Slot;
  department: Department;
  price: number;
  colors: string[];
  formality: number; // 1 athleisure ... 5 formal
  style_tags: string[];
  season: string[];
  image: string; // image URL
  url: string; // retailer page
};

// POST /profile (ProfileRequest) -> StyleProfile, built from photos and saved
// GET /profile -> StyleProfile, or 404 when the user has none yet
// PUT /profile (StyleProfile) -> StyleProfile, the user's edits
export type ProfileRequest = { photos: Item[] };

// Asset ids, so the app can show the photos again without the server storing them.
export type Look = { name: string; photo_ids: string[] };

export type ClosetId = `closet_${number}`;

// A garment the user already owns, tagged by Gemini from one of their photos. Never bought.
export type ClosetItem = {
  id: ClosetId; // unique within the user's profile
  description: string; // "navy oxford shirt"
  slot: Slot;
  colors: string[];
  formality: number;
  style_tags: string[];
  photo_id: string; // asset id of the photo it came from, so the app can show it
};

export type StyleProfile = {
  summary: string;
  style_tags: string[]; // same vocabulary as CatalogItem.style_tags
  colors: string[]; // colors the user wears most
  avoid: string[]; // style tags or colors to leave out, such as "logos"
  departments: ('men' | 'women')[]; // catalog sections to show; unisex items always show
  looks: Look[];
  closet: ClosetItem[];
};

// POST /outfits (OutfitsRequest) -> OutfitsResponse
export type Occasion =
  | 'everyday'
  | 'work'
  | 'date'
  | 'party'
  | 'formal'
  | 'active'
  | 'wedding_guest'
  | 'interview'
  | 'brunch'
  | 'travel'
  | 'concert'
  | 'outdoors'
  | 'campus'
  | 'lounge';
export type GeneratedBy = 'our-llama' | 'base-llama' | 'gemini';

export type Anchor =
  | { source: 'catalog'; id: string } // a CatalogItem.id
  | { source: 'closet'; id: ClosetId }; // a ClosetItem.id from the user's profile

export type OutfitsRequest = {
  anchor: Anchor | null; // null means "I need an outfit for..." with no anchor
  budget_min: number; // 0 or more, at most budget_max
  budget_max: number;
  max_item_price?: number | null; // above 0; no single catalog item may cost more
  occasion: Occasion;
  // "Make it nicer": ids of the outfit's items and owned pieces. The backend returns one
  // pricier version with the budget range moved up to (that outfit's total, total + $150],
  // so it can exceed budget_max. The checkout mandate is what refuses it.
  upgrade_of?: string[] | null;
};

export type Outfit = {
  id: string; // opaque; the backend doesn't store outfits
  items: CatalogItem[]; // what would be bought, a catalog anchor included
  owned: ClosetItem[]; // pieces from the user's closet; free and never in the cart
  total: number; // sum of `items` prices only, computed by the backend and rounded to cents
  reason: string;
  // Item id -> up to 3 same-slot alternatives that keep the total within the budget range.
  // The anchor and owned pieces have none. The app swaps locally, re-adds the prices,
  // and keeps looking up swaps under the original id.
  swaps: Record<string, CatalogItem[]>;
};

// A 503 when every generator fails, never an empty list.
export type OutfitsResponse = {
  outfits: Outfit[]; // 1 to 3, normally 2 or 3
  generated_by: GeneratedBy; // covers every outfit; label anything that isn't 'our-llama'
};

// POST /tryon (TryOnRequest) -> TryOnResponse
export type TryOnRequest = { photo: Item; item_ids: string[] }; // photo: full-body, of the user
export type TryOnResponse = { image_base64: string }; // JPEG

// POST /checkout/mandate (MandateRequest) -> Mandate
// POST /checkout/cart (CartRequest) -> CartVerdict, checked before Face ID
// POST /checkout/confirm (CartRequest) -> Receipt, or 409 if the cart no longer fits
// limit: the app defaults it to the request's budget_max. hours defaults to 24.
export type MandateRequest = { limit: number; hours?: number };

// "Visa •••• 1234, agent card": the Stripe Issuing card's last 4. The agent never sees the card number.
export type CardRef = { label: string };

export type Mandate = {
  id: string;
  limit: number;
  spent: number;
  category: 'apparel';
  expires_at: string; // ISO 8601
  card: CardRef;
};

export type CartRequest = { mandate_id: string; item_ids: string[] };

export type RefusalReason = 'over_limit' | 'expired' | 'not_apparel';

// `total` is always computed by the backend from catalog prices, never taken from the app.
export type CartVerdict =
  | { status: 'allowed'; total: number; remaining: number }
  | {
      status: 'refused';
      total: number;
      remaining: number;
      reason: RefusalReason;
      message: string; // shown to the user
      suggestion: Outfit | null; // the closest outfit that fits
    };

export type Receipt = {
  order_id: string;
  items: CatalogItem[];
  total: number;
  remaining: number;
  card: CardRef;
  authorization_id: string | null; // Stripe Issuing's iauth_...; null means a simulated payment
  created_at: string; // ISO 8601
};

// GET /rate/next -> RatePair
// POST /rate (RateChoice) -> 204
export type RatePair = {
  pair_id: string;
  request: OutfitsRequest; // the request both outfits answer
  profile_summary: string;
  a: Outfit;
  b: Outfit; // only the backend knows which model made which
};

export type RateChoice = { pair_id: string; choice: 'a' | 'b' };

// DELETE /me -> 204, after deleting the user's profile, feedback and mandates
