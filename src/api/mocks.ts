import type {
  CartRequest,
  CartVerdict,
  CatalogItem,
  ClosetItem,
  Mandate,
  MandateRequest,
  Outfit,
  OutfitsRequest,
  OutfitsResponse,
  RatePair,
  Receipt,
  Slot,
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
    // Stand-in for the real product page so the retailer links can be tried.
    url: `https://www.google.com/search?q=${encodeURIComponent(name)}`,
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
  // Cheap pieces, so a small budget like $10–$40 still gets outfits.
  item('top_050', 'Basic white tee', 'top', 12, 'white'),
  item('top_053', 'Ribbed tank', 'top', 15, 'black'),
  item('bottom_021', 'Cotton pull-on shorts', 'bottom', 18, 'navy'),
  item('shoes_030', 'Canvas slip-ons', 'shoes', 24, 'black'),
  item('accessory_009', 'Ribbed beanie', 'accessory', 14, 'olive'),
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

// The slots each outfit fills. A dress replaces the top and bottom.
const LOOKS: Slot[][] = [
  ['top', 'bottom', 'outerwear', 'shoes'],
  ['top', 'bottom', 'shoes'],
  ['top', 'bottom', 'shoes', 'accessory'],
];
const DRESS_LOOKS: Slot[][] = [
  ['dress', 'outerwear', 'shoes'],
  ['dress', 'shoes'],
  ['dress', 'shoes', 'accessory'],
];

// The catalog anchor of the last request, which the cart suggestion never drops.
let lastAnchorId: string | null = null;

const sum = (items: CatalogItem[]) => items.reduce((total, i) => total + i.price, 0);

// Outfits built around the picked piece, inside the budget range and the max per item,
// like the real stylist. Each outfit aims near the middle of the range, picking a
// different item per slot so the three aren't the same.
export function outfits(req: OutfitsRequest): OutfitsResponse {
  const perItem = req.max_item_price ?? Infinity;
  const pool = catalog.filter((c) => c.price <= perItem);
  const anchorItem = req.anchor?.source === 'catalog' ? byId(req.anchor.id) : null;
  const anchorOwned = req.anchor?.source === 'closet' ? profile.closet.find((c) => c.id === req.anchor!.id) : null;
  const anchorSlot = anchorItem?.slot ?? anchorOwned?.slot;
  const target = (req.budget_min + req.budget_max) / 2;
  lastAnchorId = anchorItem?.id ?? null;

  const looks = anchorSlot === 'dress' ? DRESS_LOOKS : LOOKS;
  const stamp = Date.now();
  const seen = new Set<string>();
  const list: Outfit[] = [];

  looks.forEach((slots, n) => {
    const items: CatalogItem[] = anchorItem ? [anchorItem] : [];
    const owned = anchorOwned ? [anchorOwned] : [];
    // The first outfit wears the user's own sneakers, like the stylist can with the closet.
    const mine = n === 0 && !anchorOwned ? profile.closet.find((c) => c.slot === 'shoes') : undefined;
    if (mine) owned.push(mine);
    const open = slots.filter((slot) => slot !== anchorSlot && slot !== mine?.slot);
    open.forEach((slot, k) => {
      const left = req.budget_max - sum(items);
      const share = (target - sum(items)) / (open.length - k);
      const options = pool
        .filter((c) => c.slot === slot && c.price <= left)
        .sort((a, b) => Math.abs(a.price - share) - Math.abs(b.price - share));
      if (options.length) items.push(options[n % options.length]);
    });
    const key = items.map((i) => i.id).sort().join();
    if (!items.length || seen.has(key)) return;
    seen.add(key);
    list.push({ id: `outfit_${stamp}_${n}`, items, owned, total: sum(items), reason: reasonFor(items, owned), swaps: {} });
  });

  for (const o of list) {
    // Every non-anchor item gets same-slot alternatives that keep it under budget, like the real backend.
    for (const i of o.items) {
      if (i.id === lastAnchorId) continue;
      o.swaps[i.id] = pool
        .filter((c) => c.slot === i.slot && c.id !== i.id && o.total - i.price + c.price <= req.budget_max)
        .slice(0, 3);
    }
  }
  return { outfits: list, generated_by: 'our-llama' };
}

function reasonFor(items: CatalogItem[], owned: ClosetItem[]) {
  const names = [...items.map((i) => i.name.toLowerCase()), ...owned.map((c) => `your ${c.description}`)];
  if (names.length === 1) return `Just the ${names[0]}, the only piece that fits this budget.`;
  return `The ${names[0]} with ${names.slice(1, -1).join(', ')}${names.length > 2 ? ' and ' : ''}${names.at(-1)}.`;
}

// "Make it nicer" for the checkout demo: the same outfit with the leather jacket, which
// pushes the cart over a $200 limit. Not in the API yet (backend/CHANGES_FOR_CHARLIE.md).
export function nicer(o: Outfit): Outfit {
  const moto = byId('outerwear_011');
  const items = o.items.some((i) => i.slot === 'outerwear')
    ? o.items.map((i) => (i.slot === 'outerwear' ? moto : i))
    : [...o.items, moto];
  return {
    ...o,
    id: `${o.id}_nicer`,
    items,
    total: sum(items),
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
  return sum(req.item_ids.map(byId));
}

// The closest cart under `budget`: swap the priciest piece for a cheaper one in the same
// slot, or drop it, until it fits. The picked piece always stays.
function closestUnder(ids: string[], budget: number): Outfit | null {
  const cart = ids.map(byId);
  while (sum(cart) > budget) {
    const priciest = cart.filter((i) => i.id !== lastAnchorId).sort((a, b) => b.price - a.price)[0];
    if (!priciest) return null;
    const over = sum(cart) - budget;
    const cheaper = catalog
      .filter((c) => c.slot === priciest.slot && c.price < priciest.price && !cart.includes(c))
      .sort((a, b) => b.price - a.price);
    const replacement = cheaper.find((c) => priciest.price - c.price >= over) ?? cheaper.at(-1);
    cart.splice(cart.indexOf(priciest), 1, ...(replacement ? [replacement] : []));
  }
  if (!cart.length) return null;
  return {
    id: `outfit_fit_${Date.now()}`,
    items: cart,
    owned: [],
    total: sum(cart),
    reason: 'The same look with cheaper pieces where it counts.',
    swaps: {},
  };
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
    suggestion: closestUnder(req.item_ids, remaining),
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
