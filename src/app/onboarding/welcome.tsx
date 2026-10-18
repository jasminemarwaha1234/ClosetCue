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
import { useState } from 'react';
import { StatusBar } from 'expo-status-bar';
import { router } from 'expo-router';
import { ActivityIndicator, Alert, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';

import { GoogleLogo } from '@/components/logos';
import { hasProfile } from '@/lib/onboarding';
import { continueAsGuest, getSession, signInWithGoogle } from '@/lib/supabase';
import { colors, radii, type } from '@/theme';

// Welcome + sign-in. Designed in Paper ("As If / Welcome – sign in").
// Google brings a saved profile back on any phone; a guest stays on this one.
export default function WelcomeScreen() {
  const [busy, setBusy] = useState<null | 'google' | 'guest'>(null);

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

  async function google() {
    setBusy('google');
    try {
      if (await signInWithGoogle()) await next();
    } catch (e) {
      Alert.alert("Couldn't sign in with Google", e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(null);
    }
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
    <View style={styles.container}>
      <ScrollView contentContainerStyle={styles.content}>
        <View style={styles.hero}>
          <Text style={styles.wordmark}>
            As If<Text style={styles.dot}>.</Text>
          </Text>
          <Text style={styles.tagline}>Whole outfits, built around one thing you love.</Text>
        </View>

        <View style={styles.actions}>
          <View style={styles.card}>
            <Text style={styles.cardTitle}>Sign in once, keep your style</Text>
            <Text style={styles.cardText}>
              Your profile and closet are saved to your account, so you only share photos once.
              Photos themselves are never stored.
            </Text>
          </View>

          <Pressable style={styles.button} onPress={google} disabled={busy !== null}>
            {busy === 'google' ? (
              <ActivityIndicator color={colors.onPrimary} />
            ) : (
              <>
                <View style={styles.logo}>
                  <GoogleLogo />
                </View>
                <Text style={styles.buttonText}>Continue with Google</Text>
              </>
            )}
          </Pressable>

          <View style={styles.guest}>
            <Pressable style={styles.guestButton} onPress={guest} disabled={busy !== null}>
              {busy === 'guest' ? (
                <ActivityIndicator color={colors.primary} />
              ) : (
                <Text style={styles.guestText}>Continue as guest</Text>
              )}
            </Pressable>
            <Text style={styles.note}>Guests stay on this phone. Add Google later to keep it.</Text>
          </View>
        </View>
      </ScrollView>
      <StatusBar style="dark" />
    </View>
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
    gap: 48,
  },
  hero: { gap: 16 },
  wordmark: { ...type.wordmark, color: colors.text },
  dot: { color: colors.primary },
  tagline: { ...type.lead, fontSize: 20, lineHeight: 28, color: colors.textMuted, maxWidth: 340 },
  actions: { gap: 14 },
  card: {
    backgroundColor: colors.surface,
    borderRadius: radii.xl,
    padding: 20,
    gap: 8,
  },
  cardTitle: { fontSize: 16, fontWeight: '600', lineHeight: 22, color: colors.text },
  cardText: { fontSize: 15, lineHeight: 22, color: colors.textBody },
  button: {
    flexDirection: 'row',
    gap: 10,
    height: 56,
    borderRadius: radii.pill,
    backgroundColor: colors.primary,
    alignItems: 'center',
    justifyContent: 'center',
  },
  buttonText: { ...type.button, color: colors.onPrimary },
  logo: {
    width: 28,
    height: 28,
    borderRadius: 14,
    backgroundColor: colors.background,
    alignItems: 'center',
    justifyContent: 'center',
  },
  guest: { gap: 10, alignItems: 'center' },
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
  note: { fontSize: 13, lineHeight: 18, color: colors.textMuted, textAlign: 'center' },
});
