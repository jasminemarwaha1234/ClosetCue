// import { Placeholder } from '@/components/Placeholder';

// export default function WelcomeScreen() {
//   return (
//     <Placeholder
//       description="What we read, what we keep, and the choice of how to share photos."
//       links={[
//         { label: 'Share your photos', href: '/onboarding/photos' },
//       ]}
//     />
//   );
// }
import { useEffect, useState } from 'react';
import type { Session } from '@supabase/supabase-js';
import { StatusBar } from 'expo-status-bar';
import { router } from 'expo-router';
import {
  ActivityIndicator,
  Alert,
  KeyboardAvoidingView,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';

import { AccountFields } from '@/components/AccountFields';
import { hasProfile } from '@/lib/onboarding';
import {
  continueAsGuest,
  createAccount,
  getSession,
  isGuest,
  signIn,
  signOut,
  usernameError,
  usernameOf,
} from '@/lib/supabase';
import { colors, radii, type } from '@/theme';

// Welcome + sign-in. Designed in Paper ("As If / Welcome – sign in"), with a username and
// password in place of Google for now. An account brings a saved profile back on any phone;
// a guest stays on this one.
export default function WelcomeScreen() {
  const [mode, setMode] = useState<'signin' | 'create'>('signin');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [busy, setBusy] = useState<null | 'account' | 'guest' | 'continue'>(null);
  // Already signed in (an account or a guest), from an earlier launch. Undefined while checking.
  const [current, setCurrent] = useState<Session | null | undefined>(undefined);
  const creating = mode === 'create';

  useEffect(() => {
    getSession()
      .then(setCurrent)
      .catch(() => setCurrent(null));
  }, []);

  // Someone who already finished onboarding goes straight to Build.
  async function next() {
    const session = await getSession();
    if (await hasProfile(session?.user.id)) {
      if (router.canDismiss()) router.dismissAll();
      router.replace('/build');
    } else {
      router.push('/onboarding/photos');
    }
  }

  async function submit() {
    const problem =
      usernameError(username) ?? (password.length < 6 ? 'Use a password of at least 6 characters.' : null);
    if (problem) {
      Alert.alert(creating ? "Couldn't create your account" : "Couldn't sign in", problem);
      return;
    }
    setBusy('account');
    try {
      await (creating ? createAccount(username, password) : signIn(username, password));
      setPassword('');
      await next();
    } catch (e) {
      Alert.alert(
        creating ? "Couldn't create your account" : "Couldn't sign in",
        e instanceof Error ? e.message : String(e),
      );
    } finally {
      setBusy(null);
    }
  }

  async function resume() {
    setBusy('continue');
    await next().finally(() => setBusy(null));
  }

  // Signs out so someone else can sign in. A guest's profile can't be recovered, so ask first.
  function switchAccount() {
    const out = async () => {
      await signOut();
      setCurrent(null);
    };
    if (!isGuest(current ?? null)) return void out();
    Alert.alert('Start over?', "This guest profile can't be recovered after you leave it.", [
      { text: 'Cancel', style: 'cancel' },
      { text: 'Start over', style: 'destructive', onPress: out },
    ]);
  }

  async function guest() {
    setBusy('guest');
    try {
      await continueAsGuest();
    } catch {
      // Anonymous sign-ins are off in Supabase: carry on without an account, on this phone only.
    }
    await next().finally(() => setBusy(null));
  }

  return (
    <KeyboardAvoidingView style={styles.container} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
      <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
        <View style={styles.hero}>
          <Text style={styles.wordmark}>
            As If<Text style={styles.dot}>.</Text>
          </Text>
          <Text style={styles.tagline}>Whole outfits, built around one thing you love.</Text>
        </View>

        <View style={styles.actions}>
          <View style={styles.card}>
            <Text style={styles.cardTitle}>{current ? 'Welcome back' : 'Sign in once, keep your style'}</Text>
            <Text style={styles.cardText}>
              {current
                ? 'Your profile and closet are saved, so you can pick up where you left off.'
                : 'Your profile and closet are saved to your account, so you only share photos once. Photos themselves are never stored.'}
            </Text>
          </View>

          {current === undefined ? (
            <ActivityIndicator color={colors.primary} />
          ) : current ? (
            <>
              <Pressable style={styles.button} onPress={resume} disabled={busy !== null}>
                {busy === 'continue' ? (
                  <ActivityIndicator color={colors.onPrimary} />
                ) : (
                  <Text style={styles.buttonText}>
                    {isGuest(current) ? 'Continue as guest' : `Continue as ${usernameOf(current)}`}
                  </Text>
                )}
              </Pressable>
              <Pressable onPress={switchAccount} hitSlop={8} style={styles.switch}>
                <Text style={styles.switchLink}>
                  {isGuest(current) ? 'Not you? Start over' : 'Use a different account'}
                </Text>
              </Pressable>
            </>
          ) : (
            <>
              <AccountFields
                username={username}
                password={password}
                onUsername={setUsername}
                onPassword={setPassword}
                onSubmit={submit}
                newPassword={creating}
              />

              <Pressable style={styles.button} onPress={submit} disabled={busy !== null}>
                {busy === 'account' ? (
                  <ActivityIndicator color={colors.onPrimary} />
                ) : (
                  <Text style={styles.buttonText}>{creating ? 'Create account' : 'Sign in'}</Text>
                )}
              </Pressable>
              <Pressable onPress={() => setMode(creating ? 'signin' : 'create')} hitSlop={8} style={styles.switch}>
                <Text style={styles.switchText}>
                  {creating ? 'Have an account? ' : 'New here? '}
                  <Text style={styles.switchLink}>{creating ? 'Sign in' : 'Create an account'}</Text>
                </Text>
              </Pressable>
            </>
          )}

          {current === null ? (
            <View style={styles.guest}>
              <Pressable style={styles.guestButton} onPress={guest} disabled={busy !== null}>
                {busy === 'guest' ? (
                  <ActivityIndicator color={colors.primary} />
                ) : (
                  <Text style={styles.guestText}>Continue as guest</Text>
                )}
              </Pressable>
              <Text style={styles.note}>Guests stay on this phone. Save an account later to keep it.</Text>
            </View>
          ) : null}
        </View>
      </ScrollView>
      <StatusBar style="dark" />
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background },
  content: {
    flexGrow: 1,
    justifyContent: 'space-between',
    paddingHorizontal: 24,
    paddingTop: 96,
    paddingBottom: 40,
    gap: 40,
  },
  hero: { gap: 16 },
  wordmark: { ...type.wordmark, color: colors.text },
  dot: { color: colors.primary },
  tagline: {
    ...type.lead,
    fontSize: 20,
    lineHeight: 28,
    color: colors.textMuted,
    maxWidth: 340,
  },
  actions: { gap: 14 },
  card: {
    backgroundColor: colors.surface,
    borderRadius: radii.xl,
    padding: 20,
    gap: 8,
  },
  cardTitle: {
    fontSize: 16,
    fontWeight: '600',
    lineHeight: 22,
    color: colors.text,
  },
  cardText: { fontSize: 15, lineHeight: 22, color: colors.textBody },
  button: {
    height: 56,
    borderRadius: radii.pill,
    backgroundColor: colors.primary,
    alignItems: 'center',
    justifyContent: 'center',
  },
  buttonText: { ...type.button, color: colors.onPrimary },
  switch: { alignSelf: 'center' },
  switchText: { fontSize: 15, lineHeight: 20, color: colors.textMuted },
  switchLink: { fontWeight: '600', color: colors.onPrimarySoft },
  guest: { gap: 10, alignItems: 'center', paddingTop: 6 },
  guestButton: {
    alignSelf: 'stretch',
    height: 56,
    borderRadius: radii.pill,
    borderWidth: 1.5,
    borderColor: colors.hairline,
    backgroundColor: colors.background,
    alignItems: 'center',
    justifyContent: 'center',
  },
  guestText: { ...type.button, color: colors.onPrimarySoft },
  note: {
    fontSize: 13,
    lineHeight: 18,
    color: colors.textMuted,
    textAlign: 'center',
  },
});
