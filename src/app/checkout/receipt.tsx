import { router, Stack } from 'expo-router';
import { ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { PieceImage, PrimaryButton, RetailerLink, money } from '@/components/ui';
import { payMethod } from '@/lib/payment';
import { capitalize, useSession } from '@/lib/session';
import { colors, radii, spacing } from '@/theme';

// Receipt: what was bought, what it cost, what's left of the limit, and Stripe's
// authorization ID (or a "simulated" label when there is none). Designed in Paper ("As If / Receipt").
// No order reaches the store (PLAN.md section 8), so it says so and links each item to its real page.
export default function ReceiptScreen() {
  const { receipt, mandate, chosen, payMethodId } = useSession();

  if (!receipt) {
    return (
      <View style={styles.center}>
        <Text style={styles.muted}>No purchase yet.</Text>
      </View>
    );
  }

  const owned = chosen?.owned ?? [];
  const limit = mandate?.limit ?? receipt.total + receipt.remaining;
  const used = limit > 0 ? Math.min((limit - receipt.remaining) / limit, 1) : 1;

  return (
    <SafeAreaView style={styles.screen} edges={['top', 'bottom']}>
      <Stack.Screen options={{ headerShown: false, gestureEnabled: false }} />
      <ScrollView contentContainerStyle={styles.content}>
        <View style={styles.hero}>
          <View style={styles.check}>
            <Text style={styles.checkMark}>✓</Text>
          </View>
          <View style={styles.heroText}>
            <Text style={styles.eyebrow}>{receipt.authorization_id ? 'PAID' : 'PAID (SIMULATED)'}</Text>
            <Text style={styles.title}>{money(receipt.total)}, done.</Text>
            <Text style={styles.lead}>
              {receipt.items.map((i) => i.name).join(', ')}.
              {owned.length ? ` Your ${owned.map((c) => c.description).join(' and ')} are already yours.` : ''}
            </Text>
          </View>
          <View style={styles.demo}>
            <Text style={styles.demoText}>Demo: no order was placed and no money moved.</Text>
          </View>
        </View>

        <View>
          {receipt.items.map((i) => (
            <View key={i.id} style={styles.item}>
              <PieceImage image={i.image} colorName={i.colors[0]} style={styles.thumb} />
              <View style={styles.itemText}>
                <Text style={styles.itemName} numberOfLines={1}>
                  {i.name}
                </Text>
                <RetailerLink url={i.url} />
              </View>
              <Text style={styles.itemPrice}>{money(i.price)}</Text>
            </View>
          ))}
        </View>

        <View>
          <Row label="Bought" value={`${receipt.items.length} ${receipt.items.length === 1 ? 'piece' : 'pieces'}`} />
          <Row label="Paid with" value={`${payMethod(payMethodId).label} (demo)`} />
          <Row label="Agent card" value={capitalize(receipt.card.label)} />
          <Row
            label={receipt.authorization_id ? 'Stripe authorization' : 'Payment'}
            value={receipt.authorization_id ?? 'Simulated, no card charged'}
          />
        </View>

        <View style={styles.limit}>
          <View style={styles.limitHeader}>
            <Text style={styles.limitTitle}>Left on your limit</Text>
            <View style={styles.limitAmount}>
              <Text style={styles.stat}>{money(receipt.remaining)}</Text>
              <Text style={styles.of}>of {money(limit)}</Text>
            </View>
          </View>
          <View style={styles.track}>
            <View style={[styles.fill, { width: `${used * 100}%` }]} />
          </View>
          <Text style={styles.limitMeta}>
            The agent can spend at most {money(receipt.remaining)} more before the limit ends.
          </Text>
        </View>

        <PrimaryButton label="Done" onPress={() => router.dismissTo('/build')} style={styles.done} />
      </ScrollView>
    </SafeAreaView>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <View style={styles.row}>
      <Text style={styles.rowLabel}>{label}</Text>
      <Text style={styles.rowValue} numberOfLines={1}>
        {value}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: colors.background },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center', backgroundColor: colors.background },
  content: { flexGrow: 1, padding: spacing.lg, paddingTop: 40, gap: 28 },
  hero: { gap: spacing.md },
  check: {
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: colors.primary,
    alignItems: 'center',
    justifyContent: 'center',
  },
  checkMark: { fontSize: 26, fontWeight: '700', color: colors.onPrimary },
  heroText: { gap: 8 },
  eyebrow: { fontSize: 14, lineHeight: 18, fontWeight: '600', letterSpacing: 1.1, color: colors.primary },
  title: { fontSize: 44, lineHeight: 48, fontWeight: '800', letterSpacing: -1.5, color: colors.text },
  lead: { fontSize: 17, lineHeight: 24, color: colors.textMuted },
  demo: {
    alignSelf: 'flex-start',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: radii.md,
    backgroundColor: colors.surface,
  },
  demoText: { fontSize: 14, lineHeight: 20, fontWeight: '500', color: colors.textBody },
  item: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: colors.hairline,
  },
  thumb: { width: 40, height: 46, borderRadius: radii.sm },
  itemText: { flex: 1, gap: 2, alignItems: 'flex-start' },
  itemName: { fontSize: 15, lineHeight: 20, fontWeight: '500', color: colors.text },
  itemPrice: { fontSize: 15, lineHeight: 20, fontWeight: '600', color: colors.text },
  row: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    gap: spacing.md,
    paddingVertical: 14,
    borderBottomWidth: 1,
    borderBottomColor: colors.hairline,
  },
  rowLabel: { fontSize: 15, lineHeight: 20, color: colors.textMuted },
  rowValue: { flexShrink: 1, fontSize: 15, lineHeight: 20, fontWeight: '600', color: colors.text },
  limit: { gap: 12, padding: spacing.md, borderRadius: radii.xl, backgroundColor: colors.surface },
  limitHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'baseline' },
  limitTitle: { fontSize: 16, lineHeight: 20, fontWeight: '600', color: colors.text },
  limitAmount: { flexDirection: 'row', alignItems: 'baseline', gap: 4 },
  stat: { fontSize: 24, lineHeight: 28, fontWeight: '800', letterSpacing: -0.72, color: colors.text },
  of: { fontSize: 15, lineHeight: 20, color: colors.textMuted },
  track: { height: 8, borderRadius: 4, backgroundColor: colors.hairline, overflow: 'hidden' },
  fill: { height: 8, borderRadius: 4, backgroundColor: colors.primary },
  limitMeta: { fontSize: 14, lineHeight: 20, color: colors.textBody },
  done: { marginTop: 'auto' },
  muted: { fontSize: 14, color: colors.textMuted },
});
