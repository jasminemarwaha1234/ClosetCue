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
  OutfitsRequest,
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
  // True while GET /profile is in flight, so screens can tell "loading" from "no profile yet".
  profileLoading: boolean;
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
  const [profileLoading, setProfileLoading] = useState(true);
  const [payMethodId, setPayMethodId] = useState<PayMethodId>('apple_pay');

  // Load the profile and catalog. Again after signing in (an account or a guest), since the
  // profile belongs to the account. Separately, so the catalog loads before onboarding makes the profile.
  useEffect(() => {
    const load = () => {
      setProfileLoading(true);
      getProfile()
        .then(setProfile)
        .catch(() => {})
        .finally(() => setProfileLoading(false));
      getCatalog().then(setCatalog).catch(() => {});
    };
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

  // Build starts with no piece picked, so people choose their own first. Signing out (above)
  // clears the piece, so the next account starts empty too.

  const shop = useMemo(() => forDepartments(catalog, profile), [catalog, profile]);

  const value: Session = {
    profile,
    profileLoading,
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
  { value: 'formal', label: 'Formal' },
  { value: 'semi-formal', label: 'Semi-formal' },
  { value: 'work', label: 'Work' },
  { value: 'everyday', label: 'Everyday' },
  { value: 'party', label: 'Party' },
  { value: 'casual', label: 'Casual' },
  { value: 'athletic', label: 'Athletic' },
  { value: 'comfy', label: 'Comfy' },
];

// POST /outfits for what the user picked on Build.
export function outfitsRequest(s: Pick<Session, 'anchor' | 'budget' | 'maxItemPrice' | 'occasion'>): OutfitsRequest {
  return {
    anchor: s.anchor,
    budget_min: s.budget[0],
    budget_max: s.budget[1],
    max_item_price: s.maxItemPrice,
    occasion: s.occasion,
  };
}

export const occasionLabel = (o: Occasion) => OCCASIONS.find((x) => x.value === o)?.label ?? o;

export const capitalize = (s: string) => s.charAt(0).toUpperCase() + s.slice(1);
