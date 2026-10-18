import { useCallback, useEffect, useState } from 'react';
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { getRatePair, sendRate } from '@/api/client';
import type { Outfit, RatePair } from '@/api/types';
import { Header, PieceImage, TextButton, money } from '@/components/ui';
import { occasionLabel, useSession } from '@/lib/session';
import { colors, radii, spacing } from '@/theme';

// 8. Which is better? Two outfits for the same request, one from base Llama and one from our
// model, in random order with no labels. Designed in Paper ("Fitly / Rate").
export default function RateScreen() {
  const { catalog } = useSession();
  const [pair, setPair] = useState<RatePair | null>(null);
  const [picked, setPicked] = useState<'a' | 'b' | null>(null);
  const [rated, setRated] = useState(0);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setPair(null);
    setPicked(null);
    setError(null);
    try {
      setPair(await getRatePair());
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }, []);

  useEffect(() => {
    getRatePair()
      .then(setPair)
      .catch((e) => setError(e instanceof Error ? e.message : String(e)));
  }, []);

  async function choose(choice: 'a' | 'b') {
    if (!pair || picked) return;
    setPicked(choice);
    try {
      await sendRate({ pair_id: pair.pair_id, choice });
      setRated((n) => n + 1);
      load();
    } catch (e) {
      setPicked(null);
      setError(e instanceof Error ? e.message : String(e));
    }
  }

  // "$50–$200 · everyday · cream crewneck"
  function requestLabel(p: RatePair) {
    const r = p.request;
    const anchor =
      r.anchor === null
        ? 'no piece picked'
        : r.anchor.source === 'closet'
          ? 'a piece they own'
          : (catalog.find((c) => c.id === r.anchor!.id)?.name.toLowerCase() ?? 'a picked piece');
    return `${money(r.budget_min)}–${money(r.budget_max)} · ${occasionLabel(r.occasion).toLowerCase()} · ${anchor}`;
  }

  return (
    <SafeAreaView style={styles.screen} edges={['top']}>
      <ScrollView contentContainerStyle={styles.content}>
        <Header
          eyebrow="Rate"
          title="Which is better?"
          lead="Same request, two stylists. We won't say which is which."
        />

        {error ? (
          <View style={styles.center}>
            <Text style={styles.muted}>{error}</Text>
            <TextButton label="Try again" onPress={load} />
          </View>
        ) : !pair ? (
          <View style={styles.center}>
            <ActivityIndicator color={colors.primary} />
          </View>
        ) : (
          <>
            <View style={styles.request}>
              <Text style={styles.requestText}>{requestLabel(pair)}</Text>
            </View>
            <OutfitOption label="Outfit A" outfit={pair.a} selected={picked === 'a'} onPress={() => choose('a')} />
            <OutfitOption label="Outfit B" outfit={pair.b} selected={picked === 'b'} onPress={() => choose('b')} />
            <Text style={styles.hint}>
              Tap the one you'd rather wear{rated > 0 ? ` · ${rated} rated` : ''}
            </Text>
          </>
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

function OutfitOption({
  label,
  outfit,
  selected,
  onPress,
}: {
  label: string;
  outfit: Outfit;
  selected: boolean;
  onPress: () => void;
}) {
  const colorsShown = [...outfit.items.map((i) => i.colors[0]), ...outfit.owned.map((c) => c.colors[0])];
  return (
    <Pressable onPress={onPress} style={[styles.option, selected && styles.optionSelected]}>
      <View style={styles.optionHeader}>
        <Text style={styles.optionTitle}>{label}</Text>
        <Text style={[styles.optionTotal, selected && styles.optionTotalSelected]}>{money(outfit.total)}</Text>
      </View>
      <View style={styles.pieces}>
        {colorsShown.slice(0, 4).map((c, n) => (
          <PieceImage key={n} colorName={c} dashed={n >= outfit.items.length} style={styles.piece} />
        ))}
      </View>
      <Text style={styles.reason}>{outfit.reason}</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: colors.background },
  content: { padding: spacing.lg, paddingTop: 8, gap: spacing.md },
  center: { alignItems: 'center', gap: spacing.sm, paddingTop: 60 },
  muted: { fontSize: 15, lineHeight: 22, color: colors.textMuted, textAlign: 'center' },
  request: {
    alignSelf: 'flex-start',
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 18,
    borderWidth: 1,
    borderColor: colors.hairline,
  },
  requestText: { fontSize: 14, lineHeight: 18, fontWeight: '600', color: colors.text },
  option: {
    gap: 12,
    padding: 18,
    borderRadius: radii.xl,
    borderWidth: 1.5,
    borderColor: colors.hairline,
  },
  optionSelected: { borderWidth: 2, borderColor: colors.primary, backgroundColor: colors.surface },
  optionHeader: { flexDirection: 'row', justifyContent: 'space-between' },
  optionTitle: { fontSize: 16, lineHeight: 20, fontWeight: '600', color: colors.text },
  optionTotal: { fontSize: 16, lineHeight: 20, fontWeight: '700', color: colors.text },
  optionTotalSelected: { color: colors.onPrimarySoft },
  pieces: { flexDirection: 'row', gap: 8 },
  piece: { flex: 1, height: 80 },
  reason: { fontSize: 14, lineHeight: 20, color: colors.textMuted },
  hint: { fontSize: 15, lineHeight: 20, color: colors.textMuted, textAlign: 'center', paddingTop: 8 },
});
