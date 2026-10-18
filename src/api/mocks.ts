import type {
  CartRequest,
  CartVerdict,
  CatalogItem,
  Mandate,
  MandateRequest,
  Outfit,
  OutfitsRequest,
  OutfitsResponse,
  RatePair,
  Receipt,
  StyleProfile,
} from './types';

// Fake responses in the shapes of src/api/types.ts, so the app works before the
// backend does. The client uses these while EXPO_PUBLIC_USE_MOCKS isn't "false".

function item(
  id: string,
  name: string,
  slot: CatalogItem['slot'],
  price: number,
  color: string,
  extra: Partial<CatalogItem> = {},
): CatalogItem {
  return {
    id,
    name,
    brand: 'Sample brand',
    slot,
    department: 'unisex',
    price,
    colors: [color],
    formality: 2,
    style_tags: ['minimal', 'relaxed'],
    season: ['fall', 'winter', 'spring'],
    image: '',
    url: '',
    ...extra,
  };
}

export const catalog: CatalogItem[] = [
  item('top_012', 'Relaxed cotton crewneck', 'top', 38, 'cream'),
  item('top_020', 'Black merino tee', 'top', 32, 'black'),
  item('top_031', 'Striped boat-neck top', 'top', 44, 'navy', { department: 'women' }),
  item('top_044', 'White oxford shirt', 'top', 48, 'white', { department: 'men', formality: 3 }),
  item('bottom_004', 'Olive straight chino', 'bottom', 54, 'olive'),
  item('bottom_009', 'Black wide trousers', 'bottom', 64, 'black', { formality: 3 }),
  item('bottom_015', 'Light-wash straight jeans', 'bottom', 58, 'denim'),
  item('dress_003', 'Black slip dress', 'dress', 78, 'black', { department: 'women', formality: 4 }),
  item('outerwear_002', 'Navy chore jacket', 'outerwear', 62, 'navy'),
  item('outerwear_007', 'Olive overshirt', 'outerwear', 56, 'olive'),
  item('outerwear_011', 'Leather moto jacket', 'outerwear', 152, 'brown', { formality: 3 }),
  item('shoes_009', 'White canvas sneakers', 'shoes', 30, 'white'),
  item('shoes_014', 'Lilac low-tops', 'shoes', 45, 'lilac'),
  item('shoes_021', 'Brown leather loafers', 'shoes', 88, 'brown', { formality: 4 }),
  item('accessory_005', 'Canvas tote', 'accessory', 22, 'tan'),
];

const byId = (id: string) => catalog.find((c) => c.id === id)!;

export const profile: StyleProfile = {
  summary: 'Mostly neutrals with one accent color, relaxed fits, smart-casual. Avoids logos.',
  style_tags: ['minimal', 'relaxed', 'smart-casual', 'neutral tones'],
  colors: ['cream', 'black', 'olive', 'navy'],
  formality: 2,
  avoid: ['logos', 'neon'],
  departments: ['men', 'women'],
  looks: [
    { name: 'Weekend errands', photo_ids: [] },
    { name: 'Work casual', photo_ids: [] },
  ],
  closet: [
    {
      id: 'closet_1',
      description: 'navy oxford shirt',
      slot: 'top',
      colors: ['navy'],
      formality: 3,
      style_tags: ['smart-casual'],
      photo_id: '',
    },
    {
      id: 'closet_2',
      description: 'white canvas sneakers',
      slot: 'shoes',
      colors: ['white'],
      formality: 2,
      style_tags: ['minimal'],
      photo_id: '',
    },
    {
      id: 'closet_3',
      description: 'tan suede jacket',
      slot: 'outerwear',
      colors: ['tan'],
      formality: 3,
      style_tags: ['relaxed'],
      photo_id: '',
    },
  ],
};

function outfit(id: string, itemIds: string[], reason: string, ownedIds: string[] = []): Outfit {
  const items = itemIds.map(byId);
  return {
    id,
    items,
    owned: profile.closet.filter((c) => ownedIds.includes(c.id)),
    total: items.reduce((sum, i) => sum + i.price, 0),
    reason,
    swaps: {},
  };
}

export function outfits(req: OutfitsRequest): OutfitsResponse {
  const anchor = req.anchor?.source === 'catalog' ? req.anchor.id : null;
  const list = [
    outfit(
      'outfit_1',
      ['top_012', 'bottom_004', 'outerwear_002'],
      'The navy jacket keeps it sharp, and your own white sneakers echo the cream knit.',
      ['closet_2'],
    ),
    outfit(
      'outfit_2',
      ['top_012', 'bottom_009', 'outerwear_007', 'shoes_014'],
      'Black trousers dress up the crewneck, and the lilac shoes are the one accent.',
    ),
    outfit(
      'outfit_3',
      ['top_012', 'bottom_015', 'shoes_009', 'accessory_005'],
      'Light denim and white canvas keep the cream knit easy for a day out.',
    ),
  ];
  for (const o of list) {
    // Every non-anchor item gets same-slot alternatives, like the real backend.
    for (const i of o.items) {
      if (i.id === anchor) continue;
      o.swaps[i.id] = catalog.filter((c) => c.slot === i.slot && c.id !== i.id).slice(0, 3);
    }
  }
  return { outfits: list, generated_by: 'our-llama' };
}

// "Make it nicer" for the checkout demo: the same outfit with the leather jacket, which
// pushes the cart over a $200 limit. Not in the API yet (backend/CHANGES_FOR_CHARLIE.md).
export function nicer(o: Outfit): Outfit {
  const items = o.items.map((i) => (i.slot === 'outerwear' ? byId('outerwear_011') : i));
  return {
    ...o,
    id: `${o.id}_nicer`,
    items,
    total: items.reduce((sum, i) => sum + i.price, 0),
    reason: 'A leather moto jacket makes the whole look sharper.',
    swaps: {},
  };
}

let mandate: Mandate | null = null;

export function createMandate(req: MandateRequest): Mandate {
  const hours = req.hours ?? 24;
  mandate = {
    id: `mandate_${Date.now()}`,
    limit: req.limit,
    spent: 0,
    category: 'apparel',
    expires_at: new Date(Date.now() + hours * 3600_000).toISOString(),
    card: { label: 'Visa •••• 4242, agent card' },
  };
  return mandate;
}

function cartTotal(req: CartRequest) {
  return req.item_ids.reduce((sum, id) => sum + byId(id).price, 0);
}

export function checkCart(req: CartRequest): CartVerdict {
  const limit = mandate?.limit ?? 0;
  const total = cartTotal(req);
  const remaining = limit - (mandate?.spent ?? 0);
  if (total <= remaining) return { status: 'allowed', total, remaining: remaining - total };
  return {
    status: 'refused',
    total,
    remaining,
    reason: 'over_limit',
    message: `This cart is $${total - remaining} over your $${limit} limit.`,
    suggestion: outfit(
      'outfit_fit',
      ['top_012', 'bottom_004', 'outerwear_002'],
      'The chore jacket keeps the same shape for less.',
      ['closet_2'],
    ),
  };
}

export function confirm(req: CartRequest): Receipt {
  const total = cartTotal(req);
  if (mandate) mandate.spent += total;
  return {
    order_id: `order_${Date.now()}`,
    items: req.item_ids.map(byId),
    total,
    remaining: (mandate?.limit ?? 0) - (mandate?.spent ?? 0),
    card: mandate?.card ?? { label: 'Visa •••• 4242, agent card' },
    authorization_id: null, // mocks are always a simulated payment
    created_at: new Date().toISOString(),
  };
}

export function ratePair(n: number): RatePair {
  const a = outfit(`pair_${n}_a`, ['top_012', 'bottom_004', 'outerwear_002', 'shoes_009'], '');
  const b = outfit(`pair_${n}_b`, ['top_012', 'bottom_009', 'outerwear_007', 'shoes_014'], '');
  a.reason = 'Cream knit, olive chinos, navy jacket, white sneakers.';
  b.reason = 'Cream knit, black trousers, olive overshirt, lilac sneakers.';
  return {
    pair_id: `pair_${n}`,
    request: {
      anchor: { source: 'catalog', id: 'top_012' },
      budget_min: 50,
      budget_max: 200,
      occasion: 'everyday',
    },
    profile_summary: profile.summary,
    a: n % 2 ? b : a,
    b: n % 2 ? a : b,
  };
}
