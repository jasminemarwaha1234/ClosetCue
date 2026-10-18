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
import { StatusBar } from 'expo-status-bar';
import { Link } from 'expo-router';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';

import { colors, radii, type } from '@/theme';

// Welcome + consent. Designed in Paper ("Fitly / Home" frame).
export default function WelcomeScreen() {
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
            <Text style={styles.cardTitle}>What we read, what we keep</Text>
            <Text style={styles.cardText}>
              We look through your newest photos to learn your style, and you choose how many to
              share. Thumbnails are checked on our server and not stored. Full-size photos never
              leave your phone.
            </Text>
          </View>

          <Link href="/onboarding/photos" asChild>
            <Pressable style={styles.button}>
              <Text style={styles.buttonText}>Share your photos</Text>
            </Pressable>
          </Link>
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
  actions: { gap: 20 },
  card: {
    backgroundColor: colors.surface,
    borderRadius: radii.xl,
    padding: 20,
    gap: 8,
  },
  cardTitle: { fontSize: 16, fontWeight: '600', lineHeight: 22, color: colors.text },
  cardText: { fontSize: 15, lineHeight: 22, color: colors.textBody },
  button: {
    height: 56,
    borderRadius: radii.pill,
    backgroundColor: colors.primary,
    alignItems: 'center',
    justifyContent: 'center',
  },
  buttonText: { ...type.button, color: colors.onPrimary },
});
