import 'expo-sqlite/localStorage/install';
import { createClient, type Session } from '@supabase/supabase-js';

// The phone only talks to Supabase to sign in (PLAN.md section 4). Every read and write goes
// through the backend, which checks the access token we send it and holds the service key.
//
// Two ways in, from the welcome screen: a username and password, or a guest (Supabase's
// anonymous sign-in). A guest can save their account later from Your style and keeps it.

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

export async function getSession(): Promise<Session | null> {
  if (!supabase) return null;
  const { data } = await supabase.auth.getSession();
  return data.session;
}

// The signed-in user's access token, or null before they sign in or continue as a guest.
export async function accessToken(): Promise<string | null> {
  return (await getSession())?.access_token ?? null;
}

export const isGuest = (session: Session | null) => session?.user.is_anonymous ?? true;

export async function continueAsGuest() {
  if (!supabase) return; // no project yet: the app runs on mocks
  const { error } = await supabase.auth.signInAnonymously();
  if (error) throw error;
}

// Accounts are a username and password. Supabase signs in with an email, so each username maps
// to an address on a domain nobody receives mail at. That only works with "Confirm email" off
// (Authentication -> Sign In / Providers -> Email), so Supabase never tries to send to it.
const ACCOUNT_DOMAIN = 'users.asif.app';

export const USERNAME_RULE = /^[a-z0-9_.]{3,20}$/;

export function usernameError(username: string): string | null {
  return USERNAME_RULE.test(username.trim().toLowerCase())
    ? null
    : 'Usernames are 3 to 20 letters, numbers, dots or underscores.';
}

const emailFor = (username: string) => `${username.trim().toLowerCase()}@${ACCOUNT_DOMAIN}`;

// The username back from a session, for "Signed in as …".
export const usernameOf = (session: Session | null) =>
  (session?.user.user_metadata?.username as string | undefined) ?? session?.user.email?.split('@')[0] ?? null;

// Supabase's messages, in the app's words.
function friendly(message: string): Error {
  if (/invalid login credentials/i.test(message)) return new Error('Wrong username or password.');
  if (/already (registered|been registered)|already exists/i.test(message)) return new Error('That username is taken.');
  if (/password should be at least/i.test(message)) return new Error('Use a password of at least 6 characters.');
  return new Error(message);
}

// Creating an account with "Confirm email" on would make Supabase email the made-up address,
// and bounced mail can get the project's email sending restricted. So check first.
async function requireNoEmailConfirmation() {
  const res = await fetch(`${url}/auth/v1/settings`, { headers: { apikey: key! } });
  const settings: { mailer_autoconfirm?: boolean } = await res.json();
  if (!settings.mailer_autoconfirm) {
    throw new Error('Turn off "Confirm email" in Supabase first (Authentication → Sign In / Providers → Email).');
  }
}

export async function signIn(username: string, password: string) {
  if (!supabase) throw new Error("Accounts aren't set up yet. Continue as a guest.");
  const { error } = await supabase.auth.signInWithPassword({ email: emailFor(username), password });
  if (error) throw friendly(error.message);
}

export async function createAccount(username: string, password: string) {
  if (!supabase) throw new Error("Accounts aren't set up yet. Continue as a guest.");
  await requireNoEmailConfirmation();
  const { data, error } = await supabase.auth.signUp({
    email: emailFor(username),
    password,
    options: { data: { username: username.trim().toLowerCase() } },
  });
  if (error) throw friendly(error.message);
  if (!data.session) {
    // Supabase is waiting for an email confirmation that can never arrive.
    throw new Error('Turn off "Confirm email" in Supabase (Authentication → Sign In / Providers → Email).');
  }
}

// A guest keeps their account, profile and closet by giving it a username and password.
// Needs "Allow manual linking" on, and "Confirm email" off so the address counts as verified.
export async function saveGuestAccount(username: string, password: string) {
  if (!supabase) throw new Error("Accounts aren't set up yet.");
  await requireNoEmailConfirmation();
  const name = username.trim().toLowerCase();
  const linked = await supabase.auth.updateUser({ email: emailFor(name), data: { username: name } });
  if (linked.error) throw friendly(linked.error.message);
  const withPassword = await supabase.auth.updateUser({ password });
  if (withPassword.error) throw friendly(withPassword.error.message);
}

// Also used by "Delete my data", so the next launch starts at the welcome screen.
export async function signOut() {
  await supabase?.auth.signOut();
}
