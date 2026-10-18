import 'expo-sqlite/localStorage/install';
import { createClient } from '@supabase/supabase-js';

// The phone only talks to Supabase to sign in (PLAN.md section 4). Every read and write goes
// through the backend, which checks the access token we send it and holds the service key.

const url = process.env.EXPO_PUBLIC_SUPABASE_URL;
const key = process.env.EXPO_PUBLIC_SUPABASE_KEY; // the publishable (anon) key, never a secret key

// Null until both values are in .env, so the app still runs on mocks without a project.
export const supabase =
  url && key
    ? createClient(url, key, {
        auth: {
          storage: localStorage, // keeps the session across app launches
          autoRefreshToken: true,
          persistSession: true,
          detectSessionInUrl: false,
        },
      })
    : null;

let signingIn: Promise<string | null> | null = null;

// The signed-in user's access token. Signs in anonymously the first time, so there's no
// sign-up screen; the saved session is reused after that.
export function accessToken(): Promise<string | null> {
  if (!supabase) return Promise.resolve(null);
  signingIn ??= (async () => {
    const { data } = await supabase.auth.getSession();
    if (data.session) return data.session.access_token;
    const { data: created, error } = await supabase.auth.signInAnonymously();
    if (error) throw error;
    return created.session?.access_token ?? null;
  })().finally(() => {
    signingIn = null;
  });
  return signingIn;
}

// "Delete my data" also signs out, so the next launch starts a fresh anonymous account.
export async function signOut() {
  await supabase?.auth.signOut();
}
