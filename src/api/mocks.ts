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
    url: '',
    ...extra,
  };
}

// Real products from the scraped catalog (training/catalog_raw.json), with the same ids, so
// try-on and "View at retailer" work on them. Colors and formality are hand-tagged until
// Charlie's tagged catalog.json replaces these.
export const catalog: CatalogItem[] = [
  item('top_126', 'Stratus sweatshirt', 'top', 38.99, 'gray', {
    brand: "Outdoor Voices",
    department: 'unisex',
    image: "https://cdn.shopify.com/s/files/1/0190/1390/files/stratus-sweatshirt-outdoor-voices-grey-comfort-cloudknit_1.jpg",
    url: "https://www.outdoorvoices.com/products/stratus-sweatshirt-heather-grey",
  }),
  item('top_123', 'Everyday classic longsleeve', 'top', 28.99, 'white', {
    brand: "Outdoor Voices",
    department: 'unisex',
    image: "https://cdn.shopify.com/s/files/1/0190/1390/files/everyday-classic-longsleeve-outdoor-voices-white-organic-cotton.jpg",
    url: "https://www.outdoorvoices.com/products/m-everyday-classic-longsleeve-brilliant-white",
  }),
  item('top_060', 'Contrast stitch mini tank', 'top', 29, 'black', {
    brand: "Big Bud Press",
    department: 'unisex',
    image: "https://cdn.shopify.com/s/files/1/0775/2355/files/01ECOMMMINITANKSJULIETBLACKLBYMIGUEL7-9-260248.png",
    url: "https://bigbudpress.com/products/contrast-stitch-mini-tank-basic-black",
  }),
  item('top_159', 'Soft merino tee', 'top', 45, 'cream', {
    brand: "Allbirds",
    department: 'women',
    image: "https://cdn.shopify.com/s/files/1/1104/4168/products/Anytime_Tee_Natural_White_F_0201.png",
    url: "https://www.allbirds.com/products/womens-soft-merino-tee",
  }),
  item('top_153', 'Ribbed scoop neck tee', 'top', 15.2, 'gray', {
    brand: "Edikted",
    department: 'women',
    image: "https://cdn.shopify.com/s/files/1/0467/4148/7783/files/s25385_light-gray-melange_01-09-2621_1f73931f-8979-4868-9781-49d17538dbc8.jpg",
    url: "https://edikted.com/products/s25385_light-gray-melange",
  }),
  item('bottom_121', 'Zephyr pant', 'bottom', 38.99, 'navy', {
    brand: "Outdoor Voices",
    department: 'men',
    image: "https://cdn.shopify.com/s/files/1/0190/1390/files/zephyr-pant-outdoor-voices-navy-lightweight-performance-recpoly.jpg",
    url: "https://www.outdoorvoices.com/products/m-zephyr-pant-navy",
  }),
  item('bottom_126', 'RecTrek cropped wide leg pant', 'bottom', 38.97, 'beige', {
    brand: "Outdoor Voices",
    department: 'unisex',
    image: "https://cdn.shopify.com/s/files/1/0190/1390/files/W702555-DCW-BNE_RecTrekCroppedWideLegPant_Bone_000.jpg",
    url: "https://www.outdoorvoices.com/products/w-rectrek-cropped-wide-leg-pant-bone",
  }),
  item('bottom_093', 'Seventyseven cord utility shorts', 'bottom', 40, 'brown', {
    brand: "Outerknown",
    department: 'men',
    image: "https://cdn.shopify.com/s/files/1/2445/4975/files/1710033_outerknown_SeventysevenCordUtilityShort_PMN_f_pdp_bf1f29df-6362-4f0b-9dd5-2711322b3b28.jpg",
    url: "https://www.outerknown.com/products/seventyseven-cord-utility-shorts-lejp_3lc6x-resale",
  }),
  item('bottom_147', 'Washed low rise baggy jeans', 'bottom', 55, 'denim', {
    brand: "Edikted",
    department: 'women',
    image: "https://cdn.shopify.com/s/files/1/0467/4148/7783/files/s25081_plum_s14091T_blue-raw-washed_02-09-267_76141d9c-5a8d-4371-a49e-a14175a3e3f9.jpg",
    url: "https://edikted.com/products/s14091t_indigo-blue-raw-washed",
  }),
  item('dress_021', 'Jersey t-shirt dress', 'dress', 49, 'black', {
    brand: "Faherty",
    department: 'women',
    image: "https://cdn.shopify.com/s/files/1/0359/8357/files/SP26-Faherty-Womens-WDS2639-WBK-RecycledCottonJerseyTShirtDress-WashedBlack_OM_FULL_BODY_1_Web.jpg",
    url: "https://fahertybrand.com/products/recycled-cotton-jersey-t-shirt-dress-washed-black",
  }),
  item('outerwear_061', 'Sunwashed organic hoodie', 'outerwear', 49, 'navy', {
    brand: "Faherty",
    department: 'women',
    image: "https://cdn.shopify.com/s/files/1/0359/8357/files/WKS2414-NBZ_Sunwashed_Slub_Hoodie_LD_FRONT_1_Web.jpg",
    url: "https://fahertybrand.com/products/sunwashed-slub-hoodie-navy-blazer",
  }),
  item('outerwear_120', 'Sirus jacket', 'outerwear', 59.99, 'khaki', {
    brand: "Steve Madden",
    department: 'women',
    image: "https://cdn.shopify.com/s/files/1/2170/8465/files/STEVEMADDEN_APPAREL_BN302143_KHAKI-FAB_07.jpg",
    url: "https://www.stevemadden.com/products/bn302143-khaki-fab",
  }),
  item('outerwear_035', 'Kenne shirt jacket', 'outerwear', 152.6, 'blue', {
    brand: "Taylor Stitch",
    department: 'men',
    formality: 3,
    image: "https://cdn.shopify.com/s/files/1/0070/1922/files/kenne-shirt-jacket-in-blue-fog-cotton-wool-crepe-2607_001_cb35ef69-134c-4ce8-82bc-a6940d44e4f0.jpg",
    url: "https://www.taylorstitch.com/products/kenne-shirt-jacket-in-blue-fog-cotton-wool-crepe-2607",
  }),
  item('shoes_049', 'Canvas cruiser slip-on', 'shoes', 75, 'white', {
    brand: "Allbirds",
    department: 'men',
    image: "https://cdn.shopify.com/s/files/1/1104/4168/files/A12364_26Q1_Cruiser-Slip-On-Canvas-Warm-White-Natural-White_PDP_LEFT.png",
    url: "https://www.allbirds.com/products/mens-cruiser-slip-on-canvas-warm-white",
  }),
  item('shoes_054', 'Tree Runner Go', 'shoes', 65, 'white', {
    brand: "Allbirds",
    department: 'men',
    image: "https://cdn.shopify.com/s/files/1/1104/4168/files/A11484_25Q2_Tree_Runner_Go_Utility_Natural_White_Rustic_Brown_Natural_White_PDP_LEFT-2000x2000.png",
    url: "https://www.allbirds.com/products/mens-tree-runner-go-utility-natural-white-rustic-brown",
  }),
  item('shoes_004', 'Stan Smith', 'shoes', 75, 'green', {
    brand: "Brain Dead",
    department: 'unisex',
    image: "https://cdn.shopify.com/s/files/1/0642/8893/files/Brain_Dead_x_Adidas_Dark_Green_Stan_Smith_Side_optimized.jpg",
    url: "https://wearebraindead.com/products/brain-dead-x-adidas-stan-smith-dark-green",
  }),
  item('accessory_014', 'Fantasy Fest tote', 'accessory', 20, 'cream', {
    brand: "Brain Dead",
    department: 'unisex',
    image: "https://cdn.shopify.com/s/files/1/0642/8893/files/Fantasy_Games_Tote_Natural_Back_optimized.jpg",
    url: "https://wearebraindead.com/products/brain-dead-fantasy-fest-tote-bag-natural",
  }),
  item('accessory_117', 'Washed hat', 'accessory', 12.97, 'black', {
    brand: "Outdoor Voices",
    department: 'unisex',
    image: "https://cdn.shopify.com/s/files/1/0190/1390/files/washed-hat-outdoor-voices-washed-black-topstitching.jpg",
    url: "https://www.outdoorvoices.com/products/washed-hat-washed-black",
  }),
];

const byId = (id: string) => catalog.find((c) => c.id === id)!;

export const profile: StyleProfile = {
  summary: 'Mostly neutrals with one accent color, relaxed fits, smart-casual. Avoids logos.',
  style_tags: ['minimal', 'relaxed', 'smart-casual', 'neutral tones'],
  colors: ['cream', 'black', 'olive', 'navy'],
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

// The three hand-made looks the stylist starts from, around the gray sweatshirt.
const LOOKS = [
  {
    items: ['top_126', 'bottom_121', 'outerwear_061'],
    owned: ['closet_2'],
    reason: 'The navy hoodie and pant keep the gray sweatshirt easy, and your own white sneakers lift it.',
  },
  {
    items: ['top_060', 'bottom_126', 'outerwear_120', 'shoes_054'],
    owned: [],
    reason: 'A black tank under the khaki jacket, with bone wide-leg pants and white runners to keep it neutral.',
  },
  {
    items: ['top_123', 'bottom_147', 'shoes_049', 'accessory_014'],
    owned: [],
    reason: 'A white longsleeve with washed baggy jeans and white slip-ons, and a natural tote to carry it all.',
  },
];

// The catalog anchor of the last request, which the cart suggestion never drops.
let lastAnchorId: string | null = null;

// Rounded to cents, like the backend's totals.
const sum = (items: CatalogItem[]) => Math.round(items.reduce((total, i) => total + i.price, 0) * 100) / 100;

// Swaps the priciest pieces (never the anchor) for cheaper ones in the same slot, or
// drops them, until the cart is at most `budget`.
function fitUnder(cart: CatalogItem[], budget: number, keep: string | null) {
  cart = [...cart];
  while (sum(cart) > budget) {
    const priciest = cart.filter((i) => i.id !== keep).sort((a, b) => b.price - a.price)[0];
    if (!priciest) break;
    const over = sum(cart) - budget;
    const cheaper = catalog
      .filter((c) => c.slot === priciest.slot && c.price < priciest.price && !cart.includes(c))
      .sort((a, b) => b.price - a.price);
    const replacement = cheaper.find((c) => priciest.price - c.price >= over) ?? cheaper.at(-1);
    cart.splice(cart.indexOf(priciest), 1, ...(replacement ? [replacement] : []));
  }
  return cart;
}

// The three looks, rebuilt around the picked piece: it takes the place of whatever was in
// its slot (a dress replaces the top and bottom), then pieces get cheaper until the look fits
// the budget and the max per item, like the real stylist would.
export function outfits(req: OutfitsRequest): OutfitsResponse {
  const perItem = req.max_item_price ?? Infinity;
  const anchorItem = req.anchor?.source === 'catalog' ? byId(req.anchor.id) : null;
  const anchorOwned = req.anchor?.source === 'closet' ? profile.closet.find((c) => c.id === req.anchor!.id) : null;
  const anchorSlot = anchorItem?.slot ?? anchorOwned?.slot;
  const replaced: Slot[] = anchorSlot === 'dress' ? ['top', 'bottom', 'dress'] : anchorSlot ? [anchorSlot] : [];
  lastAnchorId = anchorItem?.id ?? null;
  const stamp = Date.now();
  const seen = new Set<string>();
  const list: Outfit[] = [];

  LOOKS.forEach((look, n) => {
    let items = look.items.map(byId).filter((i) => !replaced.includes(i.slot));
    let owned = profile.closet.filter((c) => look.owned.includes(c.id) && !replaced.includes(c.slot));
    if (anchorItem) items.unshift(anchorItem);
    if (anchorOwned) owned = [anchorOwned, ...owned];
    // Pieces over the max per item become the priciest one in that slot that's under it.
    items = items.flatMap((i) => {
      if (i.id === lastAnchorId || i.price <= perItem) return [i];
      const under = catalog.filter((c) => c.slot === i.slot && c.price <= perItem).sort((a, b) => b.price - a.price);
      return under[0] ? [under[0]] : [];
    });
    items = fitUnder(items, req.budget_max, lastAnchorId);
    const key = items.map((i) => i.id).sort().join();
    if (!items.length || seen.has(key)) return;
    seen.add(key);
    const untouched = !anchorSlot || (anchorItem?.id === 'top_126' && sum(items) === sum(look.items.map(byId)));
    list.push({
      id: `outfit_${stamp}_${n}`,
      items,
      owned,
      total: sum(items),
      reason: untouched ? look.reason : reasonFor(items, owned),
      swaps: {},
    });
  });

  for (const o of list) {
    // Every non-anchor item gets same-slot alternatives that keep it under budget, like the real backend.
    for (const i of o.items) {
      if (i.id === lastAnchorId) continue;
      o.swaps[i.id] = catalog
        .filter(
          (c) => c.slot === i.slot && c.id !== i.id && c.price <= perItem && o.total - i.price + c.price <= req.budget_max,
        )
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

// "Make it nicer" for the checkout demo: the same outfit with the $153 Kenne shirt jacket, which
// pushes the cart over a $200 limit.
export function nicer(o: Outfit): Outfit {
  const moto = byId('outerwear_035');
  const items = o.items.some((i) => i.slot === 'outerwear')
    ? o.items.map((i) => (i.slot === 'outerwear' ? moto : i))
    : [...o.items, moto];
  return {
    ...o,
    id: `${o.id}_nicer`,
    items,
    total: sum(items),
    reason: 'The wool-blend Kenne shirt jacket makes the whole look sharper.',
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

// The closest cart under `budget`, keeping the picked piece.
function closestUnder(ids: string[], budget: number): Outfit | null {
  const cart = fitUnder(ids.map(byId), budget, lastAnchorId);
  if (!cart.length || sum(cart) > budget) return null;
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
    message: `This cart is $${Math.round(total - remaining)} over your $${limit} limit.`,
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
  const a = outfit(`pair_${n}_a`, ['top_126', 'bottom_121', 'outerwear_061', 'shoes_049'], '');
  const b = outfit(`pair_${n}_b`, ['top_126', 'bottom_126', 'outerwear_120', 'shoes_004'], '');
  a.reason = 'Gray sweatshirt, navy pant, navy hoodie, white slip-ons.';
  b.reason = 'Gray sweatshirt, bone wide-leg pant, khaki jacket, green Stan Smiths.';
  return {
    pair_id: `pair_${n}`,
    request: {
      anchor: { source: 'catalog', id: 'top_126' },
      budget_min: 50,
      budget_max: 200,
      occasion: 'everyday',
    },
    profile_summary: profile.summary,
    a: n % 2 ? b : a,
    b: n % 2 ? a : b,
  };
}
