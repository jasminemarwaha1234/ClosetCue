import { useState } from 'react';
import { router, Stack } from 'expo-router';
import { Alert, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';

import { getOutfits } from '@/api/client';
import type { Outfit, Retry } from '@/api/types';
import { Header, OutlineButton, PieceImage, RetailerLink, money } from '@/components/ui';
import { capitalize, occasionLabel, outfitsRequest, useAnchorItem, useSession } from '@/lib/session';
import { colors, radii, spacing } from '@/theme';

const FALLBACK_LABEL = {
  'base-llama': 'Made by base Llama, because our trained model is offline.',
  gemini: 'Made by Gemini, because our trained model is offline.',
} as const;

// For each outfit, which alternative each item is swapped to (index into [original, ...swaps]).
type SwapState = Record<string, Record<string, number>>;

// The outfit with the user's swaps applied, the pieces they removed left out, and the total re-added.
function applyEdits(o: Outfit, picks: Record<string, number> = {}, removed: string[] = []): Outfit {
  const items = o.items
    .filter((i) => !removed.includes(i.id))
    .map((i) => {
      const n = picks[i.id] ?? 0;
      return n === 0 ? i : (o.swaps[i.id]?.[n - 1] ?? i);
    });
  return { ...o, items, total: items.reduce((sum, i) => sum + i.price, 0) };
}

const swapped = (o: Outfit, picks: Record<string, number> = {}) => applyEdits(o, picks).items;

// 5. Outfits. Designed in Paper ("ClosetCue / Outfits").
export default function OutfitsScreen() {
  const s = useSession();
  const anchorItem = useAnchorItem();
  const [open, setOpen] = useState(0);
  const [swaps, setSwaps] = useState<SwapState>({});
  // For each outfit, the original ids of the pieces the user doesn't want to buy.
  const [removed, setRemoved] = useState<Record<string, string[]>>({});
  const [retrying, setRetrying] = useState(false);
  // True once these outfits came from the user asking for Gemini, not from a fallback.
  const [retried, setRetried] = useState(false);

  const anchorId = s.anchor?.id;
  const turnedDown = s.generatedBy === 'our-llama' || s.generatedBy === 'base-llama' ? s.generatedBy : null;
  const shown = s.outfits.map((o) => applyEdits(o, swaps[o.id], removed[o.id]));
  const anchorName =
    anchorItem?.catalog?.name.split(' ').pop()?.toLowerCase() ??
    anchorItem?.closet?.description.split(' ').pop();

  // Cycles one piece through [original, ...alternatives]. Swaps are keyed by the original item's id.
  function swap(o: Outfit, originalId: string) {
    const count = (o.swaps[originalId]?.length ?? 0) + 1;
    const now = swaps[o.id]?.[originalId] ?? 0;
    setSwaps({ ...swaps, [o.id]: { ...swaps[o.id], [originalId]: (now + 1) % count } });
  }

  // Leave a piece out of the cart, or put it back. At least one piece stays.
  function toggleRemoved(o: Outfit, originalId: string) {
    const now = removed[o.id] ?? [];
    const next = now.includes(originalId) ? now.filter((id) => id !== originalId) : [...now, originalId];
    if (next.length >= o.items.length) return;
    setRemoved({ ...removed, [o.id]: next });
  }

  // Gemini answers instead, never with an outfit shown here (OutfitsRequest.retry). Takes ~30 s, up to 60.
  async function retry(generatedBy: Retry['generated_by']) {
    setRetrying(true);
    try {
      const res = await getOutfits({
        ...outfitsRequest(s),
        retry: { generated_by: generatedBy, outfits: s.outfits.map((o) => [...o.items, ...o.owned].map((i) => i.id)) },
      });
      s.setOutfits(res.outfits);
      s.setGeneratedBy(res.generated_by);
      setOpen(0);
      setSwaps({});
      setRemoved({});
      setRetried(true);
    } catch (e) {
      Alert.alert("Couldn't ask Gemini", e instanceof Error ? e.message : String(e));
    } finally {
      setRetrying(false);
    }
  }

  function go(o: Outfit, to: 'tryon' | 'checkout') {
    s.setChosen(o);
    if (to === 'tryon') router.push({ pathname: '/tryon/[outfitId]', params: { outfitId: o.id } });
    else router.push('/checkout');
  }

  return (
    <>
      <Stack.Screen
        options={{ title: `${money(s.budget[0])}–${money(s.budget[1])} · ${occasionLabel(s.occasion)}` }}
      />
      <ScrollView style={styles.screen} contentContainerStyle={styles.content}>
        <Header
          eyebrow={`${shown.length} outfits`}
          title={anchorName ? `Built around your ${anchorName}` : `Ready for ${occasionLabel(s.occasion).toLowerCase()}`}
        />

        {retried ? (
          <Text style={styles.asked}>Made by Gemini, as you asked.</Text>
        ) : s.generatedBy && s.generatedBy !== 'our-llama' ? (
          <Text style={styles.fallback}>{FALLBACK_LABEL[s.generatedBy]}</Text>
        ) : null}

        {shown.map((o, index) =>
          index === open ? (
            <View key={o.id} style={styles.card}>
              <View style={styles.cardHeader}>
                <Text style={styles.cardTitle}>Outfit {index + 1}</Text>
                <Text style={styles.total}>{money(o.total)}</Text>
              </View>

              <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.pieces}>
                {swapped(s.outfits[index], swaps[o.id]).map((i, n) => {
                  const original = s.outfits[index].items[n];
                  const isAnchor = s.anchor?.source === 'catalog' && original.id === anchorId;
                  const isRemoved = removed[o.id]?.includes(original.id) ?? false;
                  const canSwap = !isAnchor && !isRemoved && (s.outfits[index].swaps[original.id]?.length ?? 0) > 0;
                  const canRemove = isRemoved || o.items.length > 1;
                  return (
                    <View key={original.id} style={styles.piece}>
                      <View style={isRemoved && styles.removed}>
                        <PieceImage image={i.image} colorName={i.colors[0]} style={styles.pieceImage} />
                        {isAnchor ? (
                          <View style={styles.badge}>
                            <Text style={styles.badgeText}>PICKED</Text>
                          </View>
                        ) : null}
                        {canSwap ? (
                          <Pressable
                            onPress={() => swap(s.outfits[index], original.id)}
                            style={styles.swap}
                            hitSlop={4}
                            accessibilityLabel={`Swap ${i.name}`}
                          >
                            <Text style={styles.swapText}>⇄ Swap</Text>
                          </Pressable>
                        ) : null}
                      </View>
                      {canRemove ? (
                        <Pressable
                          onPress={() => toggleRemoved(s.outfits[index], original.id)}
                          style={[styles.corner, isRemoved && styles.addBack]}
                          hitSlop={6}
                          accessibilityLabel={isRemoved ? `Add ${i.name} back` : `Don't buy ${i.name}`}
                        >
                          <Text style={[styles.cornerIcon, isRemoved && styles.addBackIcon]}>
                            {isRemoved ? '+' : '×'}
                          </Text>
                        </Pressable>
                      ) : null}
                      <Text style={[styles.pieceName, isRemoved && styles.removedText]} numberOfLines={2}>
                        {i.name}
                      </Text>
                      {isRemoved ? (
                        <Text style={styles.piecePrice}>Not buying</Text>
                      ) : (
                        <>
                          <Text style={styles.piecePrice}>{money(i.price)}</Text>
                          <RetailerLink url={i.url} label="View" />
                        </>
                      )}
                    </View>
                  );
                })}
                {o.owned.map((c) => (
                  <View key={c.id} style={styles.piece}>
                    <PieceImage photoId={c.photo_id} colorName={c.colors[0]} dashed style={styles.pieceImage} />
                    <Text style={styles.pieceName} numberOfLines={2}>
                      {capitalize(c.description)}
                    </Text>
                    <Text style={styles.owned}>From your closet</Text>
                  </View>
                ))}
              </ScrollView>

              <Text style={styles.reason}>{o.reason}</Text>

              <View style={styles.actions}>
                <Pressable style={[styles.action, styles.actionPrimary]} onPress={() => go(o, 'tryon')}>
                  <Text style={[styles.actionText, styles.actionPrimaryText]}>Try it on</Text>
                </Pressable>
                <Pressable style={styles.action} onPress={() => go(o, 'checkout')}>
                  <Text style={styles.actionText}>Check out</Text>
                </Pressable>
              </View>
            </View>
          ) : (
            <Pressable key={o.id} style={styles.compact} onPress={() => setOpen(index)}>
              <View style={styles.swatches}>
                {[
                  ...o.items.map((i) => ({ image: i.image, colorName: i.colors[0] })),
                  ...o.owned.map((c) => ({ photoId: c.photo_id, colorName: c.colors[0] })),
                ]
                  .slice(0, 4)
                  .map((p, n) => (
                    <PieceImage key={n} {...p} style={styles.swatch} />
                  ))}
              </View>
              <View style={styles.compactText}>
                <Text style={styles.compactTitle}>Outfit {index + 1}</Text>
                <Text style={styles.compactMeta}>
                  {o.items.length} to buy{o.owned.length ? ` + ${o.owned.length} you own` : ''}
                </Text>
              </View>
              <Text style={styles.compactTotal}>{money(o.total)}</Text>
            </Pressable>
          ),
        )}

        <Text style={styles.hint}>Tap × to leave a piece out, or Swap to change it.</Text>

        {turnedDown ? (
          <View style={styles.retry}>
            <OutlineButton
              label={retrying ? 'Asking Gemini…' : 'Try again with Gemini'}
              onPress={() => retry(turnedDown)}
              disabled={retrying}
            />
            {retrying ? <Text style={styles.hint}>This can take up to a minute.</Text> : null}
          </View>
        ) : null}
      </ScrollView>
    </>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: colors.background },
  content: { padding: spacing.lg, paddingTop: 8, gap: 20 },
  fallback: {
    fontSize: 14,
    lineHeight: 20,
    color: colors.warningText,
    backgroundColor: colors.warningSurface,
    padding: spacing.sm,
    borderRadius: radii.md,
    overflow: 'hidden',
  },
  asked: { fontSize: 14, lineHeight: 20, color: colors.textMuted },
  card: { gap: spacing.md, padding: spacing.md, borderRadius: radii.xl, backgroundColor: colors.surface },
  cardHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'baseline' },
  cardTitle: { fontSize: 20, lineHeight: 24, fontWeight: '700', letterSpacing: -0.2, color: colors.text },
  total: { fontSize: 24, lineHeight: 28, fontWeight: '800', letterSpacing: -0.72, color: colors.text },
  pieces: { gap: 8 },
  piece: { width: 74, gap: 6 },
  pieceImage: { width: 74, height: 88 },
  badge: {
    position: 'absolute',
    left: 6,
    bottom: 6,
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 6,
    backgroundColor: colors.background,
  },
  badgeText: { fontSize: 11, lineHeight: 14, fontWeight: '700', letterSpacing: 0.44, color: colors.onPrimarySoft },
  corner: {
    position: 'absolute',
    right: 6,
    top: 6,
    width: 24,
    height: 24,
    borderRadius: 12,
    backgroundColor: colors.background,
    alignItems: 'center',
    justifyContent: 'center',
  },
  cornerIcon: { fontSize: 16, lineHeight: 18, fontWeight: '600', color: colors.onPrimarySoft },
  addBack: { backgroundColor: colors.primary },
  addBackIcon: { color: colors.onPrimary },
  swap: {
    position: 'absolute',
    left: 6,
    right: 6,
    bottom: 6,
    height: 24,
    borderRadius: 12,
    backgroundColor: colors.background,
    alignItems: 'center',
    justifyContent: 'center',
  },
  swapText: { fontSize: 12, lineHeight: 16, fontWeight: '600', color: colors.onPrimarySoft },
  removed: { opacity: 0.3 },
  removedText: { color: colors.textMuted, textDecorationLine: 'line-through' },
  pieceName: { fontSize: 13, lineHeight: 16, fontWeight: '600', color: colors.text },
  piecePrice: { fontSize: 13, lineHeight: 16, color: colors.textMuted },
  owned: { fontSize: 13, lineHeight: 16, fontWeight: '600', color: colors.onPrimarySoft },
  reason: { fontSize: 15, lineHeight: 22, color: colors.textBody },
  actions: { flexDirection: 'row', gap: 8 },
  action: {
    flex: 1,
    height: 48,
    borderRadius: 24,
    backgroundColor: colors.background,
    alignItems: 'center',
    justifyContent: 'center',
  },
  actionPrimary: { backgroundColor: colors.primary },
  actionText: { fontSize: 16, lineHeight: 20, fontWeight: '600', color: colors.onPrimarySoft },
  actionPrimaryText: { color: colors.onPrimary },
  compact: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 14,
    paddingVertical: 14,
    paddingHorizontal: spacing.md,
    borderWidth: 1,
    borderColor: colors.hairline,
    borderRadius: radii.xl,
  },
  swatches: { flexDirection: 'row', gap: 4 },
  swatch: { width: 28, height: 36, borderRadius: 8 },
  compactText: { flex: 1, gap: 2 },
  compactTitle: { fontSize: 16, lineHeight: 20, fontWeight: '600', color: colors.text },
  compactMeta: { fontSize: 14, lineHeight: 18, color: colors.textMuted },
  compactTotal: { fontSize: 17, lineHeight: 22, fontWeight: '700', color: colors.text },
  hint: { fontSize: 14, lineHeight: 20, color: colors.textMuted, textAlign: 'center' },
  retry: { gap: spacing.sm },
});
