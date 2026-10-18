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

export type CatalogItem = {
  id: string;
  name: string;
  brand: string;
  slot: Slot;
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

export type StyleProfile = {
  summary: string;
  style_tags: string[]; // same vocabulary as CatalogItem.style_tags
  colors: string[]; // colors the user wears most
  formality: number; // 1-5, what they usually wear
  avoid: string[]; // style tags or colors to leave out, such as "logos"
  looks: Look[];
};

// POST /outfits (OutfitsRequest) -> OutfitsResponse
export type Occasion = 'everyday' | 'work' | 'date' | 'party' | 'formal' | 'active';
export type GeneratedBy = 'our-llama' | 'base-llama' | 'gemini';

export type OutfitsRequest = {
  anchor_id: string | null; // null means "I need an outfit for..." with no anchor
  budget: number;
  occasion: Occasion;
};

export type Outfit = {
  id: string;
  items: CatalogItem[];
  total: number;
  reason: string;
  // Item id -> up to 3 same-slot alternatives that keep the total within budget.
  // The anchor has none. The app swaps locally and re-adds the prices.
  swaps: Record<string, CatalogItem[]>;
};

export type OutfitsResponse = {
  outfits: Outfit[];
  generated_by: GeneratedBy; // label anything that isn't 'our-llama'
};

// POST /tryon (TryOnRequest) -> TryOnResponse
export type TryOnRequest = { photo: Item; item_ids: string[] }; // photo: full-body, of the user
export type TryOnResponse = { image_base64: string }; // JPEG

// POST /checkout/mandate (MandateRequest) -> Mandate
// POST /checkout/cart (CartRequest) -> CartVerdict, checked before Face ID
// POST /checkout/confirm (CartRequest) -> Receipt, or 409 if the cart no longer fits
export type MandateRequest = { limit: number; hours?: number }; // hours defaults to 24

// "Visa •••• 4242, agent token". The agent never sees the card number.
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

// POST /fit (FitFeedback) -> StyleProfile, updated from the ratings
export type FitRating = 'too_small' | 'right' | 'too_big';
export type ItemFit = { item_id: string; fit: FitRating; liked: boolean };
export type FitFeedback = { order_id: string; items: ItemFit[] };

// DELETE /me -> 204, after deleting the user's profile, feedback and mandates
