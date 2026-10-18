import { getProfile, usingMocks } from '@/api/client';

// Whether this account has finished onboarding, so the app can skip the photo scan next time.
// On mocks it's remembered on the phone per account; with the real backend it's whether a profile is saved.

const key = (userId: string | undefined) => `asif.onboarded.${userId ?? 'local'}`;

export function markOnboarded(userId: string | undefined) {
  try {
    localStorage.setItem(key(userId), '1');
  } catch {}
}

export async function hasProfile(userId: string | undefined): Promise<boolean> {
  // With the real backend, only a saved profile counts: the note on the phone can be left over
  // from testing on mocks. GET /profile answers 404 when there's none yet, and api() throws.
  if (!usingMocks) {
    return getProfile().then(
      () => true,
      () => false,
    );
  }
  try {
    return Boolean(localStorage.getItem(key(userId)));
  } catch {
    return false;
  }
}

export function forgetOnboarded(userId: string | undefined) {
  try {
    localStorage.removeItem(key(userId));
  } catch {}
}
