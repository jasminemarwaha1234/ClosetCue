import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from 'react';

import { getCatalog, getProfile } from '@/api/client';
import type { PayMethodId } from '@/lib/payment';
import { supabase } from '@/lib/supabase';
import type {
  Anchor,
  CatalogItem,
  ClosetItem,
  GeneratedBy,
  Mandate,
  Occasion,
  Outfit,
  Receipt,
  StyleProfile,
} from '@/api/types';

// What the user is building, shared by Build, Pick item, Outfits, Try-on and Checkout.

// Where the budget slider's handles can stop: $5 steps at the low end, bigger jumps higher up.
export const BUDGET_STOPS = [
  10, 15, 20, 25, 30, 35, 40, 50, 60, 70, 80, 90, 100, 125, 150, 175, 200, 250, 300, 400, 500,
];

type Session = {
  profile: StyleProfile | null;
  setProfile: (p: StyleProfile) => void;
  catalog: CatalogItem[];
  // Catalog items the user can see: their departments plus unisex.
  shop: CatalogItem[];
  anchor: Anchor | null;
  setAnchor: (a: Anchor | null) => void;
  budget: [number, number];
  setBudget: (b: [number, number]) => void;
  maxItemPrice: number | null;
  setMaxItemPrice: (p: number | null) => void;
  occasion: Occasion;
  setOccasion: (o: Occasion) => void;
  // The outfits on screen, with any swaps the user made.
  outfits: Outfit[];
  setOutfits: (o: Outfit[]) => void;
  generatedBy: GeneratedBy | null;
  setGeneratedBy: (g: GeneratedBy) => void;
  // The outfit headed to try-on and checkout.
  chosen: Outfit | null;
  setChosen: (o: Outfit | null) => void;
  mandate: Mandate | null;
  setMandate: (m: Mandate | null) => void;
  receipt: Receipt | null;
  setReceipt: (r: Receipt | null) => void;
  // The picked payment method, simulated (src/lib/payment.ts).
  payMethodId: PayMethodId;
  setPayMethodId: (id: PayMethodId) => void;
};

const SessionContext = createContext<Session | null>(null);

// Catalog items the user can see: their departments plus unisex.
function forDepartments(catalog: CatalogItem[], profile: StyleProfile | null) {
  return catalog.filter(
    (c) => c.department === 'unisex' || !profile || (profile.departments as string[]).includes(c.department),
  );
}

// The catalog item that best matches the profile's style tags, picked with some
// randomness among the closest matches so the suggestion isn't always the same.
function suggestAnchor(shop: CatalogItem[], profile: StyleProfile): Anchor | null {
  const scored = shop
    .filter((c) => c.slot !== 'accessory' && !profile.avoid.some((a) => c.style_tags.includes(a)))
    .map((c) => ({ c, score: c.style_tags.filter((t) => profile.style_tags.includes(t)).length }))
    .sort((a, b) => b.score - a.score);
  const top = scored.filter((s) => s.score === scored[0]?.score).slice(0, 5);
  if (top.length === 0) return null;
  return { source: 'catalog', id: top[Math.floor(Math.random() * top.length)].c.id };
}

export function SessionProvider({ children }: { children: ReactNode }) {
  const [profile, setProfile] = useState<StyleProfile | null>(null);
  const [catalog, setCatalog] = useState<CatalogItem[]>([]);
  const [anchor, setAnchorState] = useState<Anchor | null>(null);
  const [budget, setBudget] = useState<[number, number]>([50, 200]);
  const [maxItemPrice, setMaxItemPrice] = useState<number | null>(null);
  const [occasion, setOccasion] = useState<Occasion>('everyday');
  const [outfits, setOutfits] = useState<Outfit[]>([]);
  const [generatedBy, setGeneratedBy] = useState<GeneratedBy | null>(null);
  const [chosen, setChosen] = useState<Outfit | null>(null);
  const [mandate, setMandate] = useState<Mandate | null>(null);
  const [receipt, setReceipt] = useState<Receipt | null>(null);
  const [payMethodId, setPayMethodId] = useState<PayMethodId>('apple_pay');

  // Load the profile and catalog, and prefill the anchor with a suggestion. Again after
  // signing in (Google or guest), since the profile belongs to the account.
  useEffect(() => {
    const load = () =>
      Promise.all([getProfile(), getCatalog()])
        .then(([p, c]) => {
          setProfile(p);
          setCatalog(c);
          setAnchorState((current) => current ?? suggestAnchor(forDepartments(c, p), p));
        })
        .catch(() => {});
    load();
    const sub = supabase?.auth.onAuthStateChange((event) => {
      if (event === 'SIGNED_IN') load();
      if (event === 'SIGNED_OUT') {
        setProfile(null);
        setAnchorState(null);
      }
    });
    return () => sub?.data.subscription.unsubscribe();
  }, []);

  const shop = useMemo(() => forDepartments(catalog, profile), [catalog, profile]);

  const value: Session = {
    profile,
    setProfile,
    catalog,
    shop,
    anchor,
    setAnchor: setAnchorState,
    budget,
    setBudget,
    maxItemPrice,
    setMaxItemPrice,
    occasion,
    setOccasion,
    outfits,
    setOutfits,
    generatedBy,
    setGeneratedBy,
    chosen,
    setChosen,
    mandate,
    setMandate,
    receipt,
    setReceipt,
    payMethodId,
    setPayMethodId,
  };

  return <SessionContext.Provider value={value}>{children}</SessionContext.Provider>;
}

export function useSession() {
  const s = useContext(SessionContext);
  if (!s) throw new Error('useSession must be used inside SessionProvider');
  return s;
}

// The anchor as something to show: a catalog item or a closet piece.
export function useAnchorItem(): { catalog?: CatalogItem; closet?: ClosetItem } | null {
  const { anchor, catalog, profile } = useSession();
  if (!anchor) return null;
  if (anchor.source === 'catalog') {
    const c = catalog.find((i) => i.id === anchor.id);
    return c ? { catalog: c } : null;
  }
  const o = profile?.closet.find((i) => i.id === anchor.id);
  return o ? { closet: o } : null;
}

export const OCCASIONS: { value: Occasion; label: string }[] = [
  { value: 'everyday', label: 'Everyday' },
  { value: 'work', label: 'Work' },
  { value: 'date', label: 'Date' },
  { value: 'party', label: 'Party' },
  { value: 'formal', label: 'Formal' },
  { value: 'active', label: 'Active' },
  { value: 'wedding_guest', label: 'Wedding guest' },
  { value: 'interview', label: 'Interview' },
  { value: 'brunch', label: 'Brunch' },
  { value: 'travel', label: 'Travel' },
  { value: 'concert', label: 'Concert' },
  { value: 'outdoors', label: 'Outdoors' },
  { value: 'campus', label: 'Campus' },
  { value: 'lounge', label: 'Lounge' },
];

export const occasionLabel = (o: Occasion) => OCCASIONS.find((x) => x.value === o)?.label ?? o;

export const capitalize = (s: string) => s.charAt(0).toUpperCase() + s.slice(1);
