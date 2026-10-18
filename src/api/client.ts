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

// Set in .env as EXPO_PUBLIC_API_BASE_URL (use your laptop's LAN IP on a real phone)
const API_BASE_URL = process.env.EXPO_PUBLIC_API_BASE_URL ?? 'http://localhost:8000';

// Asks the backend for the most common faces in these photos.
export async function findOwnerCandidates(thumbs: Thumb[]): Promise<Candidate[]> {
  const res = await fetch(`${API_BASE_URL}/faces/find-owner`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(thumbs.map(({ id, base64 }) => ({ id, base64 }))),
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
  });
  if (!res.ok) throw new Error(`Backend returned ${res.status}`);
  const data: { results: ScanResult[] } = await res.json();
  return data.results.filter((r) => r.has_outfit);
}

// Everything below needs the backend endpoints Person A is building. Until they're live,
// the app answers from src/api/mocks.ts. Set EXPO_PUBLIC_USE_MOCKS=false in .env to switch.
const USE_MOCKS = process.env.EXPO_PUBLIC_USE_MOCKS !== 'false';

// Every call carries the anonymous Supabase user's token, so the backend knows whose data it is.
async function api<T>(method: string, path: string, body?: unknown): Promise<T> {
  const token = await accessToken();
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

export const tryOn = (photo: Item, itemIds: string[]) =>
  USE_MOCKS
    ? Promise.reject(new Error('Try-on needs the backend. Use the flat lay for now.'))
    : api<TryOnResponse>('POST', '/tryon', { photo, item_ids: itemIds });

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
