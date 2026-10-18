// import { Placeholder } from '@/components/Placeholder';

// export default function StyleScreen() {
//   return (
//     <Placeholder
//       description="Your style profile as a short, editable summary, with your photos grouped into looks."
//       links={[
//         { label: 'Build an outfit', href: '/build' },
//       ]}
//     />
//   );
// }
import { useState } from 'react';
import { router } from 'expo-router';
import {
  ActivityIndicator,
  Alert,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';

import { putProfile } from '@/api/client';
import type { Fit, StyleProfile } from '@/api/types';
import { AccountCard } from '@/components/AccountCard';
import { capitalize, useSession } from '@/lib/session';
import { swatches } from '@/theme';

// Paper tokens ("ClosetCue / Your style"). Same names as my earlier theme file, so once your
// src/theme/index.ts has them, delete this block and use:
//   import { colors, radius, spacing, type } from '@/theme';
const colors = {
  bg: '#FFFFFF',
  text: '#17132B',
  textMuted: '#6B6585',
  accent: '#7C4DFF',
  accentDark: '#5B2FD6',
  accentTint: '#F3EEFF',
  border: '#E4DCFA',
  borderDashed: '#C9B8FF',
  white: '#FFFFFF',
  placeholderA: '#DCCFFF',
  placeholderB: '#EBE3FF',
  placeholderC: '#C9B8FF',
} as const;
const spacing = { xs: 8, sm: 12, md: 16, lg: 24, xl: 32 } as const;
const radius = { chip: 20, card: 20, thumb: 14, swatch: 24, button: 28 } as const;
const type = {
  eyebrow: { fontSize: 14, lineHeight: 18, fontWeight: '600', letterSpacing: 1.12 },
  display: { fontSize: 44, lineHeight: 48, fontWeight: '800', letterSpacing: -1.54 },
  body: { fontSize: 17, lineHeight: 24 },
  cardTitle: { fontSize: 22, lineHeight: 30, fontWeight: '600', letterSpacing: -0.22 },
  sectionTitle: { fontSize: 20, lineHeight: 24, fontWeight: '700', letterSpacing: -0.2 },
  itemTitle: { fontSize: 16, lineHeight: 20, fontWeight: '600' },
  chip: { fontSize: 15, lineHeight: 18, fontWeight: '600' },
  caption: { fontSize: 13, lineHeight: 16 },
  button: { fontSize: 17, lineHeight: 22, fontWeight: '600' },
} as const;

const PLACEHOLDERS = [colors.placeholderA, colors.placeholderB, colors.placeholderC];

const FITS: { value: Fit; label: string }[] = [
  { value: 'slim', label: 'Slim' },
  { value: 'regular', label: 'Regular' },
  { value: 'relaxed', label: 'Relaxed' },
  { value: 'oversized', label: 'Oversized' },
];

export default function StyleScreen() {
  const session = useSession();
  const profile = session.profile;
  const closet = profile?.closet ?? [];
  const [summary, setSummary] = useState<string | null>(null); // the draft while editing
  const [adding, setAdding] = useState(false);
  const [draft, setDraft] = useState('');

  // Every edit saves the whole profile (PUT /profile). It shows right away and goes back if
  // the save fails.
  async function save(updated: StyleProfile) {
    if (!profile) return;
    session.setProfile(updated);
    try {
      session.setProfile(await putProfile(updated));
    } catch (e) {
      session.setProfile(profile);
      Alert.alert("Couldn't save that", e instanceof Error ? e.message : String(e));
    }
  }

  if (!profile) {
    return (
      <View style={[styles.screen, styles.center]}>
        <ActivityIndicator color={colors.accent} />
      </View>
    );
  }

  // Removing a wrongly tagged garment saves the profile without it.
  function removeFromCloset(id: string) {
    if (!profile) return;
    save({ ...profile, closet: profile.closet.filter((c) => c.id !== id) });
    if (session.anchor?.source === 'closet' && session.anchor.id === id) session.setAnchor(null);
  }

  function toggleSummary() {
    if (!profile) return;
    if (summary === null) return setSummary(profile.summary);
    const text = summary.trim();
    if (text && text !== profile.summary) save({ ...profile, summary: text });
    setSummary(null);
  }

  function addLeaveOut() {
    if (!profile) return;
    const word = draft.trim().toLowerCase();
    if (word && !profile.avoid.includes(word)) save({ ...profile, avoid: [...profile.avoid, word] });
    setDraft('');
    setAdding(false);
  }

  function toggleFit(fit: Fit) {
    if (!profile) return;
    const fits = profile.fits.includes(fit) ? profile.fits.filter((f) => f !== fit) : [...profile.fits, fit];
    save({ ...profile, fits });
  }

  return (
    <ScrollView style={styles.screen} contentContainerStyle={styles.content}>
      <View style={styles.header}>
        <Text style={styles.eyebrow}>YOUR STYLE</Text>
        <Text style={styles.display}>Here's how you dress</Text>
        <Text style={styles.subtitle}>Read from your photos. Change anything that's off.</Text>
      </View>

      <View style={styles.summaryCard}>
        {summary !== null ? (
          <TextInput
            value={summary}
            onChangeText={setSummary}
            multiline
            autoFocus
            style={[styles.cardTitle, styles.summaryInput]}
          />
        ) : (
          <Text style={styles.cardTitle}>{profile.summary}</Text>
        )}
        <Pressable onPress={toggleSummary} style={styles.linkRow}>
          <Text style={styles.link}>{summary !== null ? 'Done' : 'Edit summary'}</Text>
        </Pressable>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Style tags</Text>
        <View style={styles.wrap}>
          {profile.style_tags.map((tag) => (
            <View key={tag} style={styles.tagChip}>
              <Text style={styles.tagText}>{tag}</Text>
            </View>
          ))}
        </View>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Colors you wear most</Text>
        <View style={styles.swatchRow}>
          {profile.colors.map((name) => (
            <View key={name} style={styles.swatchItem}>
              <View style={[styles.swatch, { backgroundColor: swatches[name] ?? colors.placeholderB }]} />
              <Text style={styles.caption}>{name}</Text>
            </View>
          ))}
        </View>
      </View>

      <View style={styles.section}>
        <View style={styles.lookHeader}>
          <Text style={styles.sectionTitle}>Fits you wear</Text>
          <Text style={styles.caption}>Tap to change</Text>
        </View>
        <View style={styles.wrap}>
          {FITS.map((f) => {
            const on = profile.fits.includes(f.value);
            return (
              <Pressable
                key={f.value}
                onPress={() => toggleFit(f.value)}
                style={[styles.fitChip, on && styles.tagChip]}
                accessibilityRole="checkbox"
                accessibilityState={{ checked: on }}
              >
                <Text style={on ? styles.tagText : styles.leaveText}>{f.label}</Text>
              </Pressable>
            );
          })}
        </View>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Leave out</Text>
        <View style={styles.wrap}>
          {profile.avoid.map((word) => (
            <Pressable
              key={word}
              onPress={() => save({ ...profile, avoid: profile.avoid.filter((w) => w !== word) })}
              style={styles.leaveChip}
            >
              <Text style={styles.leaveText}>{word}</Text>
              <Text style={styles.leaveX}>×</Text>
            </Pressable>
          ))}
          {adding ? (
            <View style={styles.addChip}>
              <TextInput
                value={draft}
                onChangeText={setDraft}
                onSubmitEditing={addLeaveOut}
                onBlur={addLeaveOut}
                autoFocus
                placeholder="e.g. leather"
                placeholderTextColor={colors.textMuted}
                style={styles.addInput}
                returnKeyType="done"
              />
            </View>
          ) : (
            <Pressable onPress={() => setAdding(true)} style={styles.addChip}>
              <Text style={styles.addText}>+ Add</Text>
            </Pressable>
          )}
        </View>
      </View>

      {closet.length ? (
        <View style={styles.section}>
          <View style={styles.lookHeader}>
            <Text style={styles.sectionTitle}>Your closet</Text>
            <Text style={styles.caption}>Found in your photos</Text>
          </View>
          <View>
            {closet.map((c) => (
              <View key={c.id} style={styles.closetRow}>
                <View
                  style={[
                    styles.closetThumb,
                    { backgroundColor: swatches[c.colors[0]?.toLowerCase()] ?? colors.placeholderB },
                  ]}
                />
                <View style={styles.closetText}>
                  <Text style={styles.closetName}>{capitalize(c.description)}</Text>
                  <Text style={styles.caption}>{capitalize(c.slot)}</Text>
                </View>
                <Pressable
                  onPress={() => removeFromCloset(c.id)}
                  hitSlop={8}
                  style={styles.closetRemove}
                  accessibilityLabel={`Remove ${c.description}`}
                >
                  <Text style={styles.leaveX}>×</Text>
                </Pressable>
              </View>
            ))}
          </View>
        </View>
      ) : null}

      <View style={[styles.section, { gap: 20 }]}>
        <Text style={styles.sectionTitle}>Your looks</Text>
        {profile.looks.map((look, li) => (
          <View key={look.name} style={styles.lookBlock}>
            <View style={styles.lookHeader}>
              <Text style={styles.itemTitle}>{look.name}</Text>
              <Text style={styles.caption}>
                {look.photo_ids.length} {look.photo_ids.length === 1 ? 'photo' : 'photos'}
              </Text>
            </View>
            <View style={styles.thumbRow}>
              {[0, 1, 2].map((i) => (
                <View
                  key={i}
                  style={[styles.thumb, { backgroundColor: PLACEHOLDERS[(i + li) % 3] }]}
                />
              ))}
            </View>
          </View>
        ))}
      </View>

      <Pressable onPress={() => router.push('/build')} style={styles.cta}>
        <Text style={styles.ctaText}>Build an outfit</Text>
      </Pressable>

      <AccountCard />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: colors.bg },
  center: { alignItems: 'center', justifyContent: 'center' },
  content: {
    paddingHorizontal: spacing.lg,
    paddingTop: 64,
    paddingBottom: 120, // clears the tab bar
    gap: spacing.xl,
  },
  header: { gap: spacing.sm },
  eyebrow: { ...type.eyebrow, color: colors.accent },
  display: { ...type.display, color: colors.text },
  subtitle: { ...type.body, color: colors.textMuted },

  summaryCard: {
    backgroundColor: colors.accentTint,
    borderRadius: radius.card,
    padding: spacing.lg,
    gap: spacing.md,
  },
  cardTitle: { ...type.cardTitle, color: colors.text },
  summaryInput: { padding: 0 },
  linkRow: { height: 24, justifyContent: 'center' },
  link: { ...type.chip, color: colors.accentDark },

  section: { gap: spacing.sm },
  sectionTitle: { ...type.sectionTitle, color: colors.text },
  wrap: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.xs },

  tagChip: {
    height: 40,
    paddingHorizontal: spacing.md,
    borderRadius: radius.chip,
    backgroundColor: colors.accentTint,
    justifyContent: 'center',
  },
  tagText: { ...type.chip, color: colors.accentDark },
  fitChip: {
    height: 40,
    paddingHorizontal: spacing.md,
    borderRadius: radius.chip,
    borderWidth: 1,
    borderColor: colors.border,
    backgroundColor: colors.white,
    justifyContent: 'center',
  },

  swatchRow: { flexDirection: 'row', gap: 20 },
  swatchItem: { alignItems: 'center', gap: spacing.xs },
  swatch: {
    width: 48,
    height: 48,
    borderRadius: radius.swatch,
        borderWidth: 1,
    borderColor: colors.border,
  },
  caption: { ...type.caption, color: colors.textMuted },

  leaveChip: {
    height: 40,
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.xs,
    paddingLeft: spacing.md,
    paddingRight: 14,
    borderRadius: radius.chip,
    borderWidth: 1,
    borderColor: colors.border,
    backgroundColor: colors.white,
  },
  leaveText: { ...type.chip, color: colors.text },
  leaveX: { fontSize: 18, lineHeight: 22, fontWeight: '500', color: colors.textMuted },
  addChip: {
    height: 40,
    minWidth: 72,
    paddingHorizontal: spacing.md,
    borderRadius: radius.chip,
    borderWidth: 1,
    borderStyle: 'dashed',
    borderColor: colors.borderDashed,
    justifyContent: 'center',
  },
  addText: { ...type.chip, color: colors.accentDark },
  addInput: { ...type.chip, color: colors.text, minWidth: 90, padding: 0 },

  closetRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
    paddingVertical: spacing.xs,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  closetThumb: { width: 40, height: 48, borderRadius: 10, borderWidth: 1, borderColor: colors.border },
  closetText: { flex: 1, gap: 2 },
  closetName: { fontSize: 15, lineHeight: 20, fontWeight: '600', color: colors.text },
  closetRemove: { width: 32, height: 32, alignItems: 'center', justifyContent: 'center' },

  lookBlock: { gap: 10 },
  lookHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'baseline' },
  itemTitle: { ...type.itemTitle, color: colors.text },
  thumbRow: { flexDirection: 'row', gap: spacing.xs },
  thumb: { width: 108, height: 140, borderRadius: radius.thumb },

  cta: {
    height: 56,
    borderRadius: radius.button,
    backgroundColor: colors.accent,
    alignItems: 'center',
    justifyContent: 'center',
  },
  ctaText: { ...type.button, color: colors.white },
});
