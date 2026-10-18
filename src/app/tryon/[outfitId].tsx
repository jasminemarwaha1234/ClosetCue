import { useState } from 'react';
import * as ImagePicker from 'expo-image-picker';
import { router, Stack } from 'expo-router';
import { ActivityIndicator, Image, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { tryOn } from '@/api/client';
import { OutlineButton, PieceImage, PrimaryButton, Segmented, money } from '@/components/ui';
import { shrinkForTryOn } from '@/lib/photos';
import { capitalize, useSession } from '@/lib/session';
import { colors, radii, spacing } from '@/theme';

type Mode = 'onyou' | 'flatlay';

// 6. Try-on: your photo wearing the outfit, with the flat lay as the fallback.
// Designed in Paper ("ClosetCue / Try-on").
export default function TryOnScreen() {
  const { chosen: outfit } = useSession();
  const [view, setView] = useState<Mode>('onyou');
  const [image, setImage] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!outfit) {
    return (
      <View style={styles.center}>
        <Text style={styles.muted}>Pick an outfit first.</Text>
      </View>
    );
  }

  // Only catalog items go to Gemini. Owned pieces are already in the user's photo.
  const ownedNote = outfit.owned.length
    ? `Your ${outfit.owned.map((c) => c.description).join(' and ')} stay as they are in your photo.`
    : null;

  async function pickAndTryOn() {
    if (!outfit) return;
    const picked = await ImagePicker.launchImageLibraryAsync({ mediaTypes: ['images'], quality: 1 });
    if (picked.canceled || !picked.assets[0]) return;
    setLoading(true);
    setError(null);
    try {
      const asset = picked.assets[0];
      const base64 = await shrinkForTryOn(asset.uri);
      if (!base64) throw new Error("Couldn't read that photo.");
      const res = await tryOn(
        { id: asset.assetId ?? asset.uri, base64 },
        outfit.items.map((i) => i.id),
      );
      setImage(`data:image/jpeg;base64,${res.image_base64}`);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }

  return (
    <SafeAreaView style={styles.screen} edges={['bottom']}>
      <Stack.Screen options={{ title: '' }} />
      <ScrollView contentContainerStyle={styles.content}>
        <Segmented
          options={[
            { value: 'onyou', label: 'On you' },
            { value: 'flatlay', label: 'Flat lay' },
          ]}
          value={view}
          onChange={setView}
        />

        {view === 'onyou' ? (
          <View style={styles.photo}>
            {image ? (
              <>
                <Image source={{ uri: image }} style={StyleSheet.absoluteFill} resizeMode="cover" />
                <View style={styles.aiChip}>
                  <Text style={styles.aiChipText}>✦ AI preview on your photo</Text>
                </View>
              </>
            ) : loading ? (
              <>
                <ActivityIndicator color={colors.primary} />
                <Text style={styles.muted}>Dressing you up. This takes 10–20 seconds.</Text>
              </>
            ) : (
              <View style={styles.empty}>
                <Text style={styles.emptyTitle}>See it on you</Text>
                <Text style={styles.muted}>Choose a full-body photo of yourself.</Text>
                {error ? <Text style={styles.error}>{error}</Text> : null}
                <OutlineButton label="Choose a photo" onPress={pickAndTryOn} style={styles.choose} />
                {ownedNote ? <Text style={styles.note}>{ownedNote}</Text> : null}
              </View>
            )}
          </View>
        ) : (
          <View style={styles.flatlay}>
            {outfit.items.map((i) => (
              <View key={i.id} style={styles.flatItem}>
                <PieceImage image={i.image} colorName={i.colors[0]} style={styles.flatImage} />
                <Text style={styles.flatName} numberOfLines={1}>
                  {i.name}
                </Text>
              </View>
            ))}
            {outfit.owned.map((c) => (
              <View key={c.id} style={styles.flatItem}>
                <PieceImage colorName={c.colors[0]} dashed style={styles.flatImage} />
                <Text style={styles.flatName} numberOfLines={1}>
                  {capitalize(c.description)} (yours)
                </Text>
              </View>
            ))}
          </View>
        )}

        <View style={styles.summary}>
          <View style={styles.summaryText}>
            <Text style={styles.summaryTitle}>This outfit</Text>
            <Text style={styles.summaryMeta} numberOfLines={2}>
              {[...outfit.items.map((i) => i.name), ...outfit.owned.map((c) => `your ${c.description}`)].join(', ')}
            </Text>
          </View>
          <Text style={styles.total}>{money(outfit.total)}</Text>
        </View>

        <PrimaryButton label="Check out" onPress={() => router.push('/checkout')} />
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: colors.background },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center', backgroundColor: colors.background },
  content: { padding: spacing.lg, paddingTop: 8, gap: spacing.md },
  photo: {
    height: 440,
    borderRadius: 24,
    backgroundColor: colors.surfaceMuted,
    alignItems: 'center',
    justifyContent: 'center',
    overflow: 'hidden',
    gap: spacing.sm,
  },
  aiChip: {
    position: 'absolute',
    left: 14,
    top: 14,
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 14,
    backgroundColor: colors.background,
  },
  aiChipText: { fontSize: 13, lineHeight: 16, fontWeight: '600', color: colors.text },
  empty: { alignItems: 'center', gap: 8, paddingHorizontal: spacing.lg },
  emptyTitle: { fontSize: 20, lineHeight: 24, fontWeight: '700', color: colors.text },
  choose: { marginTop: 8, alignSelf: 'stretch' },
  note: { fontSize: 13, lineHeight: 18, color: colors.textMuted, textAlign: 'center', marginTop: 4 },
  error: { fontSize: 14, lineHeight: 20, color: colors.error, textAlign: 'center' },
  muted: { fontSize: 14, lineHeight: 20, color: colors.textMuted, textAlign: 'center' },
  summaryMeta: { fontSize: 14, lineHeight: 20, color: colors.textMuted },
  flatlay: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
    padding: spacing.md,
    borderRadius: 24,
    backgroundColor: colors.surface,
  },
  flatItem: { width: '47%', gap: 6 },
  flatImage: { height: 150, borderRadius: radii.lg },
  flatName: { fontSize: 13, lineHeight: 16, fontWeight: '600', color: colors.text },
  summary: { flexDirection: 'row', alignItems: 'center', gap: spacing.md },
  summaryText: { flex: 1, gap: 2, alignItems: 'flex-start' },
  summaryTitle: { fontSize: 20, lineHeight: 24, fontWeight: '700', color: colors.text },
  total: { fontSize: 32, lineHeight: 36, fontWeight: '800', letterSpacing: -1, color: colors.text },
});
