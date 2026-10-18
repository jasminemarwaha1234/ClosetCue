import 'expo-sqlite/localStorage/install';
import { createClient, type Session } from '@supabase/supabase-js';
import * as Linking from 'expo-linking';
import * as WebBrowser from 'expo-web-browser';

// The phone only talks to Supabase to sign in (PLAN.md section 4). Every read and write goes
// through the backend, which checks the access token we send it and holds the service key.
//
// Two ways in, from the welcome screen: Google, or a guest (Supabase's anonymous sign-in).
// A guest can add Google later from Your style and keeps the same account and profile.

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

// Where Google sends the browser back to: exp://<laptop>/--/auth in Expo Go, lahacksai://auth
// in a build. Both must be in Supabase's Authentication -> URL Configuration -> Redirect URLs.
const redirectTo = Linking.createURL('auth');

export async function getSession(): Promise<Session | null> {
  if (!supabase) return null;
  const { data } = await supabase.auth.getSession();
  return data.session;
}

// The signed-in user's access token, or null before they choose Google or guest.
export async function accessToken(): Promise<string | null> {
  return (await getSession())?.access_token ?? null;
}

export const isGuest = (session: Session | null) => session?.user.is_anonymous ?? true;

export async function continueAsGuest() {
  if (!supabase) return; // no project yet: the app runs on mocks
  const { error } = await supabase.auth.signInAnonymously();
  if (error) throw error;
}

// Opens Google in an in-app browser and finishes the sign-in when it comes back.
// Returns false if the person closed the browser.
async function viaBrowser(startUrl: string | undefined): Promise<boolean> {
  if (!supabase || !startUrl) throw new Error("Google sign-in isn't set up yet.");
  const result = await WebBrowser.openAuthSessionAsync(startUrl, redirectTo);
  if (result.type !== 'success') return false;

  // Supabase answers with tokens in the fragment, or a code with PKCE, or an error.
  const back = new URL(result.url);
  const params = new URLSearchParams(back.hash.slice(1) || back.search.slice(1));
  const failure = params.get('error_description') ?? params.get('error');
  if (failure) throw new Error(failure.replace(/\+/g, ' '));
  const code = params.get('code');
  if (code) {
    const { error } = await supabase.auth.exchangeCodeForSession(code);
    if (error) throw error;
    return true;
  }
  const access_token = params.get('access_token');
  const refresh_token = params.get('refresh_token');
  if (!access_token || !refresh_token) throw new Error('Google sign-in came back without a session.');
  const { error } = await supabase.auth.setSession({ access_token, refresh_token });
  if (error) throw error;
  return true;
}

export async function signInWithGoogle(): Promise<boolean> {
  if (!supabase) throw new Error("Google sign-in isn't set up yet.");
  const { data, error } = await supabase.auth.signInWithOAuth({
    provider: 'google',
    options: { redirectTo, skipBrowserRedirect: true },
  });
  if (error) throw error;
  return viaBrowser(data.url);
}

// A guest adds Google to the same account, so their profile and closet stay. Needs
// "Allow manual linking" on in Supabase (Authentication -> Sign In / Providers).
export async function linkGoogle(): Promise<boolean> {
  if (!supabase) throw new Error("Google sign-in isn't set up yet.");
  const { data, error } = await supabase.auth.linkIdentity({
    provider: 'google',
    options: { redirectTo, skipBrowserRedirect: true },
  });
  if (error) throw error;
  return viaBrowser(data.url);
}

// Also used by "Delete my data", so the next launch starts at the welcome screen.
export async function signOut() {
  await supabase?.auth.signOut();
}
