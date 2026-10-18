import { useState } from 'react';
import { router } from 'expo-router';
import { FlatList, Pressable, StyleSheet, Text, TextInput, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import type { Anchor, Slot } from '@/api/types';
import { Chip, PieceImage, PrimaryButton, Segmented, TextButton, money } from '@/components/ui';
import { capitalize, useSession } from '@/lib/session';
import { colors, spacing } from '@/theme';

const SLOTS: { value: Slot | 'all'; label: string }[] = [
  { value: 'all', label: 'All' },
  { value: 'top', label: 'Tops' },
  { value: 'bottom', label: 'Bottoms' },
  { value: 'dress', label: 'Dresses' },
  { value: 'outerwear', label: 'Outerwear' },
  { value: 'shoes', label: 'Shoes' },
  { value: 'accessory', label: 'Accessories' },
];

type Tile = { anchor: Anchor; name: string; meta: string; image?: string; color?: string };

// Modal: choose the anchor from the shop, from your closet, or no piece at all.
// Designed in Paper ("As If / Pick item").
export default function PickItemScreen() {
  const s = useSession();
  const insets = useSafeAreaInsets();
  const [source, setSource] = useState<Anchor['source']>(s.anchor?.source ?? 'catalog');
  const [slot, setSlot] = useState<Slot | 'all'>('all');
  const [query, setQuery] = useState('');
  const [picked, setPicked] = useState<Anchor | null>(s.anchor);

  const q = query.trim().toLowerCase();
  const tiles: Tile[] =
    source === 'catalog'
      ? s.shop
          .filter((c) => slot === 'all' || c.slot === slot)
          .filter((c) => !q || `${c.name} ${c.brand}`.toLowerCase().includes(q))
          .map((c) => ({
            anchor: { source: 'catalog', id: c.id },
            name: c.name,
            meta: `${c.brand} · ${money(c.price)}`,
            image: c.image,
            color: c.colors[0],
          }))
      : (s.profile?.closet ?? [])
          .filter((c) => slot === 'all' || c.slot === slot)
          .filter((c) => !q || c.description.toLowerCase().includes(q))
          .map((c) => ({
            anchor: { source: 'closet', id: c.id },
            name: capitalize(c.description),
            meta: 'Yours',
            color: c.colors[0],
          }));

  const pickedName = tiles.find((t) => t.anchor.id === picked?.id)?.name;

  function done(anchor: Anchor | null) {
    s.setAnchor(anchor);
    router.back();
  }

  return (
    <View style={styles.screen}>
      <View style={styles.header}>
        <View style={styles.grabber} />
        <View style={styles.titleRow}>
          <Text style={styles.title}>Pick a piece</Text>
          <TextButton label="No piece" onPress={() => done(null)} />
        </View>
        <Segmented
          options={[
            { value: 'catalog', label: 'Shop' },
            { value: 'closet', label: 'From my closet' },
          ]}
          value={source}
          onChange={setSource}
        />
        <TextInput
          value={query}
          onChangeText={setQuery}
          placeholder={source === 'catalog' ? 'Search the shop' : 'Search your closet'}
          placeholderTextColor={colors.textMuted}
          style={styles.search}
          returnKeyType="search"
        />
        <FlatList
          horizontal
          data={SLOTS}
          keyExtractor={(x) => x.value}
          showsHorizontalScrollIndicator={false}
          style={styles.bleed}
          contentContainerStyle={styles.slots}
          renderItem={({ item }) => (
            <Chip
              variant="outline"
              label={item.label}
              selected={slot === item.value}
              onPress={() => setSlot(item.value)}
            />
          )}
        />
      </View>

      <FlatList
        data={tiles}
        keyExtractor={(t) => t.anchor.id}
        numColumns={2}
        columnWrapperStyle={styles.gridRow}
        contentContainerStyle={styles.grid}
        ListEmptyComponent={
          <Text style={styles.empty}>
            {source === 'closet' ? 'Nothing from your photos fits here yet.' : 'No matches.'}
          </Text>
        }
        renderItem={({ item: t }) => {
          const selected = picked?.id === t.anchor.id;
          return (
            <Pressable style={styles.tile} onPress={() => setPicked(t.anchor)}>
              <PieceImage
                image={t.image}
                colorName={t.color}
                dashed={t.anchor.source === 'closet'}
                style={[styles.tileImage, selected && styles.tileSelected]}
              />
              <Text style={styles.tileName} numberOfLines={1}>
                {t.name}
              </Text>
              <Text style={styles.tileMeta}>{t.meta}</Text>
            </Pressable>
          );
        }}
      />

      <View style={[styles.footer, { paddingBottom: insets.bottom + 16 }]}>
        <PrimaryButton
          label={pickedName ? `Use ${pickedName.toLowerCase()}` : 'Pick a piece'}
          disabled={!picked || !pickedName}
          onPress={() => done(picked)}
        />
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: colors.background },
  header: { gap: 14, paddingHorizontal: spacing.lg, paddingTop: 8 },
  grabber: { alignSelf: 'center', width: 40, height: 5, borderRadius: 3, backgroundColor: colors.hairline },
  titleRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  title: { fontSize: 28, lineHeight: 32, fontWeight: '800', letterSpacing: -0.84, color: colors.text },
  search: {
    height: 48,
    paddingHorizontal: spacing.md,
    borderRadius: 24,
    backgroundColor: colors.surface,
    fontSize: 16,
    color: colors.text,
  },
  bleed: { marginHorizontal: -spacing.lg, flexGrow: 0 },
  slots: { gap: 8, paddingHorizontal: spacing.lg },
  grid: { padding: spacing.lg, paddingTop: 20, gap: 20 },
  gridRow: { gap: 12 },
  tile: { flex: 1, gap: 8 },
  tileImage: { height: 168, borderRadius: 16 },
  tileSelected: { borderWidth: 3, borderColor: colors.primary },
  tileName: { fontSize: 15, lineHeight: 20, fontWeight: '600', color: colors.text },
  tileMeta: { fontSize: 14, lineHeight: 18, color: colors.textMuted, marginTop: -6 },
  empty: { fontSize: 15, color: colors.textMuted, textAlign: 'center', paddingTop: 40 },
  footer: {
    paddingHorizontal: spacing.lg,
    paddingTop: 16,
    borderTopWidth: 1,
    borderTopColor: colors.hairline,
    backgroundColor: colors.background,
  },
});
