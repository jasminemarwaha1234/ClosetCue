import { useEffect, useState } from 'react';
import type { Session } from '@supabase/supabase-js';
import { router } from 'expo-router';
import { Alert, Pressable, StyleSheet, Text, View } from 'react-native';

import { GoogleLogo } from '@/components/logos';
import { getSession, isGuest, linkGoogle, signOut, supabase } from '@/lib/supabase';
import { colors, radii, spacing } from '@/theme';

// Your account, at the bottom of Your style. A guest can add Google to keep their profile
// on any phone; a Google account can sign out.
export function AccountCard() {
  const [session, setSession] = useState<Session | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    getSession().then(setSession);
    const sub = supabase?.auth.onAuthStateChange((_event, s) => setSession(s));
    return () => sub?.data.subscription.unsubscribe();
  }, []);

  if (!supabase) return null;
  const guest = isGuest(session);

  async function saveWithGoogle() {
    setBusy(true);
    try {
      await linkGoogle();
    } catch (e) {
      Alert.alert("Couldn't add Google", e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  async function leave() {
    await signOut();
    if (router.canDismiss()) router.dismissAll();
    router.replace('/onboarding/welcome');
  }

  return (
    <View style={styles.card}>
      <Text style={styles.title}>{guest ? "You're a guest" : 'Signed in with Google'}</Text>
      <Text style={styles.text}>
        {guest
          ? 'Your profile is saved on this phone only. Add Google to keep it everywhere.'
          : `${session?.user.email ?? 'Your Google account'}. Your profile comes back on any phone.`}
      </Text>
      {guest ? (
        <Pressable
          onPress={saveWithGoogle}
          disabled={busy}
          style={({ pressed }) => [styles.google, (pressed || busy) && styles.dim]}
        >
          <GoogleLogo />
          <Text style={styles.googleText}>Save with Google</Text>
        </Pressable>
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
  google: {
    marginTop: 6,
    flexDirection: 'row',
    gap: 10,
    height: 48,
    borderRadius: 24,
    borderWidth: 1.5,
    borderColor: colors.hairline,
    alignItems: 'center',
    justifyContent: 'center',
  },
  googleText: { fontSize: 16, lineHeight: 20, fontWeight: '600', color: colors.text },
  link: { fontSize: 15, lineHeight: 20, fontWeight: '600', color: colors.onPrimarySoft, paddingTop: 4 },
  dim: { opacity: 0.6 },
});
