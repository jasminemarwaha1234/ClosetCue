import type { Thumb } from '@/lib/photos';
import type { Candidate, ScanResult } from './types';

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
