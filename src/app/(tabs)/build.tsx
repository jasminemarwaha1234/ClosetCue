import { useState } from 'react';
import { router } from 'expo-router';
import { Alert, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { getOutfits } from '@/api/client';
import { RangeSlider } from '@/components/RangeSlider';
import { Chip, Header, PieceImage, PrimaryButton, SectionTitle, money } from '@/components/ui';
import { BUDGET_STOPS, OCCASIONS, capitalize, outfitsRequest, useAnchorItem, useSession } from '@/lib/session';
import { colors, radii, spacing } from '@/theme';

const MAX_ITEM_OPTIONS: (number | null)[] = [null, 50, 100];

// 4. Build. Designed in Paper ("Fitly / Build"). Everything is prefilled, so one tap builds outfits.
export default function BuildScreen() {
  const s = useSession();
  const anchorItem = useAnchorItem();
  const [loading, setLoading] = useState(false);

  async function build() {
    setLoading(true);
    try {
      const res = await getOutfits(outfitsRequest(s));
      s.setOutfits(res.outfits);
      s.setGeneratedBy(res.generated_by);
      s.setChosen(null);
      s.setMandate(null);
      router.push('/outfits');
    } catch (e) {
      Alert.alert("Couldn't build outfits", e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }

  return (
    <SafeAreaView style={styles.screen} edges={['top']}>
      <ScrollView contentContainerStyle={styles.content}>
        <Header eyebrow="Build" title="Build a look" lead="All set. Tap once, or tweak anything." />

        <View style={styles.group}>
          <SectionTitle>{s.anchor ? 'Start with' : 'No piece picked'}</SectionTitle>
          {anchorItem ? (
            <View style={styles.anchorCard}>
              <PieceImage
                image={anchorItem.catalog?.image}
                photoId={anchorItem.closet?.photo_id}
                colorName={(anchorItem.catalog ?? anchorItem.closet)?.colors[0]}
                style={styles.anchorImage}
              />
              <View style={styles.anchorText}>
                <Text style={styles.itemTitle}>
                  {anchorItem.catalog?.name ?? capitalize(anchorItem.closet?.description ?? '')}
                </Text>
                <Text style={styles.meta}>
                  {anchorItem.catalog
                    ? `${capitalize(anchorItem.catalog.colors[0] ?? '')} · ${money(anchorItem.catalog.price)}`
                    : 'From your closet'}
                </Text>
                <View style={styles.anchorActions}>
                  <Pressable onPress={() => router.push('/pick-item')} hitSlop={8}>
                    <Text style={styles.link}>Change</Text>
                  </Pressable>
                  <Pressable onPress={() => s.setAnchor(null)} hitSlop={8}>
                    <Text style={styles.link}>Remove</Text>
                  </Pressable>
                </View>
              </View>
            </View>
          ) : (
            <Pressable onPress={() => router.push('/pick-item')} style={styles.emptyAnchor}>
              <Text style={styles.meta}>We'll build the whole outfit for your occasion.</Text>
              <Text style={styles.link}>Pick a piece</Text>
            </Pressable>
          )}
        </View>

        <View style={styles.group}>
          <View style={styles.budgetHeader}>
            <SectionTitle>Budget</SectionTitle>
            <Text style={styles.stat}>
              {money(s.budget[0])}–{money(s.budget[1])}
            </Text>
          </View>
          <RangeSlider
            stops={BUDGET_STOPS}
            value={s.budget}
            onChange={s.setBudget}
          />
          <View style={styles.rangeLabels}>
            <Text style={styles.caption}>{money(BUDGET_STOPS[0])}</Text>
            <Text style={styles.caption}>{money(BUDGET_STOPS.at(-1)!)}</Text>
          </View>
          <View style={styles.maxRow}>
            <Text style={styles.maxLabel}>Max per item</Text>
            <View style={styles.maxChips}>
              {MAX_ITEM_OPTIONS.map((p) => (
                <Chip
                  key={String(p)}
                  variant="outline"
                  label={p === null ? 'Any' : money(p)}
                  selected={s.maxItemPrice === p}
                  onPress={() => s.setMaxItemPrice(p)}
                />
              ))}
            </View>
          </View>
        </View>

        <View style={styles.group}>
          <SectionTitle>Occasion</SectionTitle>
          <ScrollView
            horizontal
            showsHorizontalScrollIndicator={false}
            style={styles.bleed}
            contentContainerStyle={styles.occasions}
          >
            {OCCASIONS.map((o) => (
              <Chip
                key={o.value}
                label={o.label}
                selected={s.occasion === o.value}
                onPress={() => s.setOccasion(o.value)}
              />
            ))}
          </ScrollView>
        </View>

        <PrimaryButton label="Build outfits" onPress={build} loading={loading} />
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: colors.background },
  content: { padding: spacing.lg, paddingTop: 8, gap: spacing.lg },
  group: { gap: spacing.sm },
  anchorCard: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.md,
    padding: spacing.sm,
    borderRadius: radii.xl,
    backgroundColor: colors.surface,
  },
  anchorImage: { width: 72, height: 88 },
  anchorText: { flex: 1, gap: 4 },
  anchorActions: { flexDirection: 'row', gap: 20, paddingTop: 4 },
  emptyAnchor: {
    padding: spacing.md,
    gap: 6,
    borderRadius: radii.xl,
    borderWidth: 1.5,
    borderStyle: 'dashed',
    borderColor: colors.dashed,
  },
  itemTitle: { fontSize: 16, lineHeight: 20, fontWeight: '600', color: colors.text },
  meta: { fontSize: 14, lineHeight: 20, color: colors.textMuted },
  link: { fontSize: 15, lineHeight: 18, fontWeight: '600', color: colors.onPrimarySoft },
  budgetHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'baseline' },
  stat: { fontSize: 32, lineHeight: 36, fontWeight: '800', letterSpacing: -1, color: colors.text },
  rangeLabels: { flexDirection: 'row', justifyContent: 'space-between', marginTop: -4 },
  caption: { fontSize: 13, lineHeight: 16, color: colors.textMuted },
  maxRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingTop: 4 },
  maxLabel: { fontSize: 15, lineHeight: 20, color: colors.textBody },
  maxChips: { flexDirection: 'row', gap: 6 },
  bleed: { marginHorizontal: -spacing.lg },
  occasions: { gap: 8, paddingHorizontal: spacing.lg },
});
