import Constants from 'expo-constants';

import type { Thumb } from '@/lib/photos';
import { accessToken, signOut } from '@/lib/supabase';
import * as mocks from './mocks';
import type {
  Candidate,
  CartRequest,
  CartVerdict,
  CatalogItem,
  Item,
  Mandate,
  MandateRequest,
  Outfit,
  OutfitsRequest,
  OutfitsResponse,
  RateChoice,
  RatePair,
  Receipt,
  ScanResult,
  StyleProfile,
  TryOnResponse,
} from './types';

// The backend. EXPO_PUBLIC_API_BASE_URL in .env wins (use it for a backend tunnel). Otherwise
// it's port 8000 on the laptop the app was loaded from, so a phone keeps finding the laptop when
// it switches between Wi-Fi and a hotspot. A tunneled app (exp.direct) can't, so it needs the env.
const devHost = Constants.expoConfig?.hostUri?.split(':')[0];
const API_BASE_URL =
  process.env.EXPO_PUBLIC_API_BASE_URL ||
  (devHost && !devHost.endsWith('exp.direct') ? `http://${devHost}:8000` : 'http://localhost:8000');

// Gives up instead of waiting forever when the backend can't be reached.
const SCAN_TIMEOUT = 90_000;
function timeout(ms: number) {
  const controller = new AbortController();
  setTimeout(() => controller.abort(), ms);
  return controller.signal;
}
const unreachable = (e: unknown) =>
  e instanceof Error && (e.name === 'AbortError' || /network request failed/i.test(e.message))
    ? new Error(`Couldn't reach the backend at ${API_BASE_URL}. Is it running, on the same Wi-Fi?`)
    : e;

// Asks the backend for the most common faces in these photos.
export async function findOwnerCandidates(thumbs: Thumb[]): Promise<Candidate[]> {
  const res = await fetch(`${API_BASE_URL}/faces/find-owner`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(thumbs.map(({ id, base64 }) => ({ id, base64 }))),
    signal: timeout(SCAN_TIMEOUT),
  }).catch((e) => {
    throw unreachable(e);
  });
  if (!res.ok) throw new Error(`Backend returned ${res.status}`);
  const data: { candidates: Candidate[] } = await res.json();
  return data.candidates;
}

// Sends one batch of thumbnails to the backend and returns the results that have an outfit.
export async function classifyBatch(batch: Thumb[], owner: number[] | null): Promise<ScanResult[]> {
  const res = await fetch(`${API_BASE_URL}/scan`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      items: batch.map(({ id, base64 }) => ({ id, base64 })),
      owner_embedding: owner,
    }),
    signal: timeout(SCAN_TIMEOUT),
  }).catch((e) => {
    throw unreachable(e);
  });
  if (!res.ok) throw new Error(`Backend returned ${res.status}`);
  const data: { results: ScanResult[] } = await res.json();
  return data.results.filter((r) => r.has_outfit);
}

// Everything below needs the backend endpoints Person A is building. Until they're live,
// the app answers from src/api/mocks.ts. Set EXPO_PUBLIC_USE_MOCKS=false in .env to switch.
const USE_MOCKS = process.env.EXPO_PUBLIC_USE_MOCKS !== 'false';
export const usingMocks = USE_MOCKS;

// Every call carries the anonymous Supabase user's token, so the backend knows whose data it is.
async function api<T>(method: string, path: string, body?: unknown): Promise<T> {
  // Before sign-in there's no token: routes that need a user answer 401, the others still work.
  const token = await accessToken().catch(() => null);
  const res = await fetch(`${API_BASE_URL}${path}`, {
    method,
    headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  if (!res.ok) {
    const detail = await res.json().then((d: { detail?: string }) => d.detail).catch(() => null);
    throw new Error(detail ?? `Backend returned ${res.status}`);
  }
  return res.status === 204 ? (undefined as T) : res.json();
}

// A short pause so mocked screens show their loading states like the real thing.
const mock = <T>(value: T) => new Promise<T>((resolve) => setTimeout(() => resolve(value), 400));

export const getCatalog = () =>
  USE_MOCKS ? mock(mocks.catalog) : api<CatalogItem[]>('GET', '/catalog');

export const getProfile = () =>
  USE_MOCKS ? mock(mocks.profile) : api<StyleProfile>('GET', '/profile');

// Gemini reads the outfit photos into a profile and closet, and the backend saves it.
export const createProfile = (photos: Thumb[]) =>
  USE_MOCKS
    ? mock(mocks.profile)
    : api<StyleProfile>('POST', '/profile', { photos: photos.map(({ id, base64 }) => ({ id, base64 })) });

export const putProfile = (profile: StyleProfile) =>
  USE_MOCKS ? mock(profile) : api<StyleProfile>('PUT', '/profile', profile);

export const getOutfits = (req: OutfitsRequest) =>
  USE_MOCKS ? mock(mocks.outfits(req)) : api<OutfitsResponse>('POST', '/outfits', req);

// One pricier version of the outfit, which may go over budget_max (OutfitsRequest.upgrade_of).
export async function makeItNicer(req: OutfitsRequest, outfit: Outfit): Promise<Outfit> {
  if (USE_MOCKS) return mock(mocks.nicer(outfit));
  const upgrade_of = [...outfit.items, ...outfit.owned].map((i) => i.id);
  const res = await api<OutfitsResponse>('POST', '/outfits', { ...req, upgrade_of });
  return res.outfits[0];
}

// Always the real backend, even on mocks: the mock catalog is real scraped products with
// the same ids, so /tryon can find their photos. Takes 10-20 seconds.
export const tryOn = (photo: Item, itemIds: string[]) =>
  api<TryOnResponse>('POST', '/tryon', { photo, item_ids: itemIds });

export const createMandate = (req: MandateRequest) =>
  USE_MOCKS ? mock(mocks.createMandate(req)) : api<Mandate>('POST', '/checkout/mandate', req);

export const checkCart = (req: CartRequest) =>
  USE_MOCKS ? mock(mocks.checkCart(req)) : api<CartVerdict>('POST', '/checkout/cart', req);

export const confirmCart = (req: CartRequest) =>
  USE_MOCKS ? mock(mocks.confirm(req)) : api<Receipt>('POST', '/checkout/confirm', req);

let ratedCount = 0;
export const getRatePair = () =>
  USE_MOCKS ? mock(mocks.ratePair(ratedCount)) : api<RatePair>('GET', '/rate/next');

export async function sendRate(choice: RateChoice): Promise<void> {
  ratedCount += 1;
  if (USE_MOCKS) return mock(undefined);
  return api<void>('POST', '/rate', choice);
}

// "Delete my data" on the Trust screen: the backend deletes the profile, feedback, mandates
// and the anonymous account, then the app signs out so the next launch starts fresh.
export async function deleteMe(): Promise<void> {
  if (!USE_MOCKS) await api<void>('DELETE', '/me');
  await signOut();
}
