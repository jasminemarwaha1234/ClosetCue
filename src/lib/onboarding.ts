import { getProfile, usingMocks } from '@/api/client';

// Whether this account has finished onboarding, so the app can skip the photo scan next time.
// Remembered on the phone per account, and with the real backend a saved profile counts too.

const key = (userId: string | undefined) => `asif.onboarded.${userId ?? 'local'}`;

export function markOnboarded(userId: string | undefined) {
  try {
    localStorage.setItem(key(userId), '1');
  } catch {}
}

export async function hasProfile(userId: string | undefined): Promise<boolean> {
  try {
    if (localStorage.getItem(key(userId))) return true;
  } catch {}
  if (usingMocks) return false;
  // GET /profile answers 404 when there's none yet, and api() throws.
  return getProfile().then(
    () => true,
    () => false,
  );
}

export function forgetOnboarded(userId: string | undefined) {
  try {
    localStorage.removeItem(key(userId));
  } catch {}
}
