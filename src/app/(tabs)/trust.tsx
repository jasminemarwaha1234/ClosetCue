import { useState, type ReactNode } from 'react';
import { router } from 'expo-router';
import { Alert, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import Svg, { Circle, Path, Rect } from 'react-native-svg';

import { deleteMe, usingMocks } from '@/api/client';
import { Header } from '@/components/ui';
import { colors, spacing } from '@/theme';

const ink = colors.onPrimarySoft;
const stroke = { fill: 'none', stroke: ink, strokeWidth: 1.8, strokeLinecap: 'round', strokeLinejoin: 'round' } as const;

const PhotoIcon = () => (
  <Svg width={22} height={22} viewBox="0 0 22 22">
    <Rect x={3} y={4.5} width={16} height={13} rx={3} {...stroke} />
    <Circle cx={8} cy={9.5} r={1.5} {...stroke} />
    <Path d="M3.5 15.5l4.5-4 3.5 3 2.5-2 5 4" {...stroke} />
  </Svg>
);
const FaceIcon = () => (
  <Svg width={22} height={22} viewBox="0 0 22 22">
    <Circle cx={11} cy={11} r={8} {...stroke} />
    <Path d="M8 13.2c.8 1 1.8 1.5 3 1.5s2.2-.5 3-1.5" {...stroke} />
    <Path d="M8.2 8.8v.4M13.8 8.8v.4" {...stroke} />
  </Svg>
);
const CardIcon = () => (
  <Svg width={22} height={22} viewBox="0 0 22 22">
    <Rect x={3} y={5.5} width={16} height={11} rx={3} {...stroke} />
    <Path d="M3 9.5h16" {...stroke} />
    <Path d="M6.5 13.5h3" {...stroke} />
  </Svg>
);
const Chevron = ({ open }: { open: boolean }) => (
  <Svg width={20} height={20} viewBox="0 0 20 20" style={{ transform: [{ rotate: open ? '90deg' : '0deg' }] }}>
    <Path d="M7.5 4.5L13 10l-5.5 5.5" {...stroke} stroke={colors.textMuted} />
  </Svg>
);

function Fact({ icon, title, children }: { icon: ReactNode; title: string; children: string }) {
  return (
    <View style={styles.fact}>
      <View style={styles.icon}>{icon}</View>
      <View style={styles.factText}>
        <Text style={styles.factTitle}>{title}</Text>
        <Text style={styles.factBody}>{children}</Text>
      </View>
    </View>
  );
}

// A row that opens in place to show its details.
function More({ title, lines, first }: { title: string; lines: string[]; first?: boolean }) {
  const [open, setOpen] = useState(false);
  return (
    <View style={[styles.more, first && styles.moreFirst]}>
      <Pressable
        onPress={() => setOpen(!open)}
        style={styles.moreHeader}
        accessibilityRole="button"
        accessibilityState={{ expanded: open }}
      >
        <Text style={styles.moreTitle}>{title}</Text>
        <Chevron open={open} />
      </Pressable>
      {open ? (
        <View style={styles.moreBody}>
          {lines.map((line) => (
            <Text key={line} style={styles.factBody}>
              {line}
            </Text>
          ))}
        </View>
      ) : null}
    </View>
  );
}

// 9. Trust: what we use, what we keep, and how to wipe it (PLAN.md section 8).
// Designed in Paper ("Fitly / Trust").
export default function TrustScreen() {
  const [deleting, setDeleting] = useState(false);

  function confirmDelete() {
    Alert.alert(
      'Delete your data?',
      usingMocks
        ? 'This is the demo build on sample data, so there is nothing saved to delete. It signs you out.'
        : 'This deletes your profile, closet, ratings and spending limits, and signs you out. It can’t be undone.',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Delete',
          style: 'destructive',
          onPress: async () => {
            setDeleting(true);
            try {
              await deleteMe();
              if (router.canDismiss()) router.dismissAll();
              router.replace('/onboarding/welcome');
            } catch (e) {
              Alert.alert("Couldn't delete your data", e instanceof Error ? e.message : String(e));
            } finally {
              setDeleting(false);
            }
          },
        },
      ],
    );
  }

  return (
    <SafeAreaView style={styles.screen} edges={['top']}>
      <ScrollView contentContainerStyle={styles.content}>
        <Header eyebrow="Trust" title="You're in control" lead="What we use, what we keep, and how to wipe it." />

        <View style={styles.facts}>
          <Fact icon={<PhotoIcon />} title="Your photos">
            Shrunk to small thumbnails on your phone. Never stored.
          </Fact>
          <Fact icon={<FaceIcon />} title="Your face">
            Used only to keep photos of you. Held in memory for the session, then gone.
          </Fact>
          <Fact icon={<CardIcon />} title="Your spending limit">
            The agent never sees your card. Anything over your limit is refused.
          </Fact>
        </View>

        <View>
          <More
            first
            title="How we use AI"
            lines={[
              'Our own trained model picks every outfit and writes why it works.',
              'Gemini reads your photos into style tags and makes the try-on images. Try-ons are AI previews, not photos.',
              'If our model is down, a backup model fills in, and the app says so.',
              'Your A/B ratings help train the next version of our model.',
            ]}
          />
          <More
            title="What this means for stores"
            lines={[
              'In this demo no order reaches a store. Each item links to its real product page.',
              "In production the agent orders through each store's own checkout, with a payment limited to that store, an amount and an expiry.",
              'Whole outfits that fit your style and budget mean fewer returns for stores.',
            ]}
          />
        </View>

        <View style={styles.footer}>
          <Pressable
            onPress={confirmDelete}
            disabled={deleting}
            style={({ pressed }) => [styles.delete, (pressed || deleting) && styles.dim]}
          >
            <Text style={styles.deleteText}>{deleting ? 'Deleting…' : 'Delete my data'}</Text>
          </Pressable>
          <Text style={styles.note}>Removes your profile and feedback for good.</Text>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: colors.background },
  content: { flexGrow: 1, padding: spacing.lg, paddingTop: 8, gap: spacing.lg },
  facts: { gap: 20 },
  fact: { flexDirection: 'row', alignItems: 'flex-start', gap: 16 },
  icon: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: colors.surface,
    alignItems: 'center',
    justifyContent: 'center',
  },
  factText: { flex: 1, gap: 4 },
  factTitle: { fontSize: 16, lineHeight: 20, fontWeight: '600', color: colors.text },
  factBody: { fontSize: 14, lineHeight: 20, color: colors.textMuted },
  more: { borderBottomWidth: 1, borderBottomColor: colors.hairline },
  moreFirst: { borderTopWidth: 1, borderTopColor: colors.hairline },
  moreHeader: { height: 48, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  moreTitle: { fontSize: 16, lineHeight: 20, fontWeight: '600', color: colors.text },
  moreBody: { gap: 8, paddingBottom: 14 },
  footer: { marginTop: 'auto', gap: 10 },
  delete: {
    height: 56,
    borderRadius: 28,
    borderWidth: 1.5,
    borderColor: colors.errorTrack,
    backgroundColor: colors.background,
    alignItems: 'center',
    justifyContent: 'center',
  },
  deleteText: { fontSize: 17, lineHeight: 22, fontWeight: '600', color: colors.error },
  note: { fontSize: 13, lineHeight: 16, color: colors.textMuted, textAlign: 'center' },
  dim: { opacity: 0.6 },
});
