import { useEffect, useState } from 'react';
import type { Session } from '@supabase/supabase-js';
import { router } from 'expo-router';
import { ActivityIndicator, Alert, Pressable, StyleSheet, Text, View } from 'react-native';

import { AccountFields } from '@/components/AccountFields';
import { getSession, isGuest, saveGuestAccount, signOut, supabase, usernameError, usernameOf } from '@/lib/supabase';
import { colors, radii, spacing } from '@/theme';

// Your account, at the bottom of Your style. A guest can save their account with a username
// and password to keep their profile on any phone; an account can sign out.
export function AccountCard() {
  const [session, setSession] = useState<Session | null>(null);
  const [saving, setSaving] = useState(false);
  const [busy, setBusy] = useState(false);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');

  useEffect(() => {
    getSession().then(setSession);
    const sub = supabase?.auth.onAuthStateChange((_event, s) => setSession(s));
    return () => sub?.data.subscription.unsubscribe();
  }, []);

  if (!supabase || !session) return null;
  const guest = isGuest(session);

  async function save() {
    const problem = usernameError(username) ?? (password.length < 6 ? 'Use a password of at least 6 characters.' : null);
    if (problem) {
      Alert.alert("Couldn't save your account", problem);
      return;
    }
    setBusy(true);
    try {
      await saveGuestAccount(username, password);
      setSaving(false);
      setPassword('');
      setSession(await getSession());
    } catch (e) {
      Alert.alert("Couldn't save your account", e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  async function leave() {
    await signOut();
    if (router.canDismiss()) router.dismissAll();
    router.replace('/onboarding/welcome');
  }

  // A guest who signs out can't get back in, so ask first.
  function startOver() {
    Alert.alert('Start over?', "You'll go back to the welcome screen. This guest profile can't be recovered.", [
      { text: 'Cancel', style: 'cancel' },
      { text: 'Start over', style: 'destructive', onPress: leave },
    ]);
  }

  return (
    <View style={styles.card}>
      <Text style={styles.title}>{guest ? "You're a guest" : `Signed in as ${usernameOf(session)}`}</Text>
      <Text style={styles.text}>
        {guest
          ? 'Your profile is saved on this phone only. Save an account to keep it everywhere.'
          : 'Your profile comes back on any phone you sign in on.'}
      </Text>
      {guest && saving ? (
        <View style={styles.form}>
          <AccountFields
            username={username}
            password={password}
            onUsername={setUsername}
            onPassword={setPassword}
            onSubmit={save}
            newPassword
          />
          <Pressable onPress={save} disabled={busy} style={({ pressed }) => [styles.button, (pressed || busy) && styles.dim]}>
            {busy ? <ActivityIndicator color={colors.onPrimary} /> : <Text style={styles.buttonText}>Save account</Text>}
          </Pressable>
        </View>
      ) : guest ? (
        <>
          <Pressable onPress={() => setSaving(true)} style={({ pressed }) => [styles.outline, pressed && styles.dim]}>
            <Text style={styles.outlineText}>Save your account</Text>
          </Pressable>
          <Pressable onPress={startOver} hitSlop={8} style={styles.startOver}>
            <Text style={styles.muted}>Not you? Start over</Text>
          </Pressable>
        </>
      ) : (
        <Pressable onPress={leave} hitSlop={8}>
          <Text style={styles.link}>Sign out</Text>
        </Pressable>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  card: { gap: 8, padding: spacing.md, borderRadius: radii.xl, borderWidth: 1, borderColor: colors.hairline },
  title: { fontSize: 16, lineHeight: 22, fontWeight: '600', color: colors.text },
  text: { fontSize: 14, lineHeight: 20, color: colors.textBody },
  form: { gap: 10, marginTop: 6 },
  button: {
    height: 48,
    borderRadius: 24,
    backgroundColor: colors.primary,
    alignItems: 'center',
    justifyContent: 'center',
  },
  buttonText: { fontSize: 16, lineHeight: 20, fontWeight: '600', color: colors.onPrimary },
  outline: {
    marginTop: 6,
    height: 48,
    borderRadius: 24,
    borderWidth: 1.5,
    borderColor: colors.hairline,
    alignItems: 'center',
    justifyContent: 'center',
  },
  outlineText: { fontSize: 16, lineHeight: 20, fontWeight: '600', color: colors.onPrimarySoft },
  link: { fontSize: 15, lineHeight: 20, fontWeight: '600', color: colors.onPrimarySoft, paddingTop: 4 },
  startOver: { alignSelf: 'center', paddingTop: 6 },
  muted: { fontSize: 14, lineHeight: 20, fontWeight: '600', color: colors.textMuted },
  dim: { opacity: 0.6 },
});
