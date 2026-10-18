import { useEffect, useState } from 'react';
import { router, Stack } from 'expo-router';
import { ActivityIndicator, Alert, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { checkCart, confirmCart, createMandate, makeItNicer } from '@/api/client';
import type { CartVerdict, Mandate, Outfit } from '@/api/types';
import { Header, OutlineButton, PieceImage, PrimaryButton, TextButton, money } from '@/components/ui';
import { confirmPayment } from '@/lib/confirm';
import { capitalize, useSession } from '@/lib/session';
import { colors, radii, spacing } from '@/theme';

function hoursLeft(m: Mandate) {
  const h = Math.max(0, Math.round((Date.parse(m.expires_at) - Date.now()) / 3600_000));
  return `Ends in ${h} ${h === 1 ? 'hour' : 'hours'}`;
}

// 7. Checkout, including the refusal. Designed in Paper ("As If / Checkout" and
// "As If / Checkout – refused"). The cart is the outfit's `items` only, never `owned`.
export default function CheckoutScreen() {
  const s = useSession();
  const outfit = s.chosen;
  const [verdict, setVerdict] = useState<CartVerdict | null>(null);
  const [previous, setPrevious] = useState<Outfit | null>(null);
  const [busy, setBusy] = useState<null | 'check' | 'pay' | 'raise' | 'nicer'>('check');

  // Make sure there's a mandate (defaulting to the budget max), then check the cart against it.
  async function fetchVerdict(o: Outfit, m: Mandate | null) {
    const mandate = m ?? (await createMandate({ limit: s.budget[1] }));
    const v = await checkCart({ mandate_id: mandate.id, item_ids: o.items.map((i) => i.id) });
    return { mandate, verdict: v };
  }

  function showVerdict(p: Promise<{ mandate: Mandate; verdict: CartVerdict }>) {
    p.then(({ mandate, verdict: v }) => {
      s.setMandate(mandate);
      setVerdict(v);
    })
      .catch((e) => Alert.alert("Couldn't check the cart", e instanceof Error ? e.message : String(e)))
      .finally(() => setBusy(null));
  }

  function check(o: Outfit, m: Mandate | null) {
    setBusy('check');
    showVerdict(fetchVerdict(o, m));
  }

  // Check again whenever the outfit changes (make it nicer, the closest one that fits, go back).
  useEffect(() => {
    if (outfit) showVerdict(fetchVerdict(outfit, s.mandate));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [outfit?.id]);

  if (!outfit || !s.mandate || !verdict) {
    return (
      <View style={styles.center}>
        {outfit ? <ActivityIndicator color={colors.primary} /> : <Text style={styles.muted}>Pick an outfit first.</Text>}
      </View>
    );
  }

  const mandate = s.mandate;
  const refused = verdict.status === 'refused';

  async function pay(m: Mandate, total: number) {
    if (!outfit) return;
    if (!(await confirmPayment(`Pay ${money(total)}`))) return;
    const receipt = await confirmCart({ mandate_id: m.id, item_ids: outfit.items.map((i) => i.id) });
    s.setReceipt(receipt);
    router.replace('/checkout/receipt');
  }

  async function payNow() {
    setBusy('pay');
    try {
      await pay(mandate, verdict!.total);
    } catch (e) {
      // 409: the cart no longer fits the mandate. Check again so the refusal shows.
      Alert.alert("Payment didn't go through", e instanceof Error ? e.message : String(e));
      check(outfit!, mandate);
    } finally {
      setBusy(null);
    }
  }

  // Only the person can raise the limit, after Face ID. The agent never can.
  async function raiseAndPay() {
    setBusy('raise');
    try {
      const raised = await createMandate({ limit: verdict!.total });
      s.setMandate(raised);
      await pay(raised, verdict!.total);
    } catch (e) {
      Alert.alert("Payment didn't go through", e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(null);
    }
  }

  async function nicer() {
    setBusy('nicer');
    try {
      const upgraded = await makeItNicer(outfit!);
      setPrevious(outfit);
      s.setChosen(upgraded);
    } catch (e) {
      Alert.alert("Couldn't make it nicer", e instanceof Error ? e.message : String(e));
      setBusy(null);
    }
  }

  function switchTo(o: Outfit) {
    setBusy('check');
    setPrevious(null);
    s.setChosen(o);
  }

  const expired = refused && verdict.reason === 'expired';
  const used = Math.min(verdict.total / mandate.limit, 1);

  return (
    <SafeAreaView style={styles.screen} edges={['bottom']}>
      <Stack.Screen options={{ title: '' }} />
      <ScrollView contentContainerStyle={styles.content}>
        <Header eyebrow="Checkout" title={refused ? "That's over your limit" : 'Ready when you are'} />

        <View style={[styles.limit, refused && styles.limitRefused]}>
          <Text style={styles.limitTitle}>Your spending limit</Text>
          <View style={styles.limitAmount}>
            <Text style={[styles.stat, refused && styles.statRefused]}>{money(verdict.total)}</Text>
            <Text style={styles.of}>of {money(mandate.limit)}</Text>
          </View>
          <View style={[styles.track, refused && styles.trackRefused]}>
            <View style={[styles.fill, refused && styles.fillRefused, { width: `${used * 100}%` }]} />
          </View>
          {refused ? (
            <Text style={styles.refusal}>
              Refused. {verdict.message}
              {verdict.reason === 'over_limit' ? " The agent can't go over it. Only you can raise it." : ''}
            </Text>
          ) : (
            <Text style={styles.limitMeta}>
              Apparel only · {hoursLeft(mandate)} · {money(verdict.remaining)} left
            </Text>
          )}
        </View>

        <View>
          <Text style={styles.section}>Cart</Text>
          {outfit.items.map((i) => (
            <View key={i.id} style={styles.row}>
              <PieceImage image={i.image} colorName={i.colors[0]} style={styles.thumb} />
              <Text style={styles.rowName}>{i.name}</Text>
              <Text style={styles.rowPrice}>{money(i.price)}</Text>
            </View>
          ))}
          {outfit.owned.length ? (
            <Text style={styles.ownedNote}>
              Not in the cart, already yours: {outfit.owned.map((c) => c.description).join(', ')}.
            </Text>
          ) : null}
        </View>

        {!refused ? (
          <View style={styles.card}>
            <View style={styles.visa}>
              <Text style={styles.visaText}>VISA</Text>
            </View>
            <View style={styles.cardText}>
              <Text style={styles.cardLabel}>{capitalize(mandate.card.label)}</Text>
              <Text style={styles.muted}>Stripe test mode. No real money moves.</Text>
            </View>
          </View>
        ) : null}

        <View style={styles.actions}>
          {!refused ? (
            <>
              <PrimaryButton label={`Pay ${money(verdict.total)}`} onPress={payNow} loading={busy === 'pay'} />
              <TextButton label="Make it nicer" onPress={nicer} />
            </>
          ) : expired ? (
            <PrimaryButton label="Start a new limit" onPress={() => check(outfit, null)} loading={busy === 'check'} />
          ) : (
            <>
              {verdict.suggestion ? (
                <PrimaryButton
                  label={`Show the closest under ${money(mandate.limit)}`}
                  onPress={() => switchTo(verdict.suggestion!)}
                />
              ) : null}
              {verdict.reason === 'over_limit' ? (
                <OutlineButton
                  label={`Raise my limit to ${money(verdict.total)} and pay`}
                  onPress={raiseAndPay}
                  loading={busy === 'raise'}
                />
              ) : null}
              {previous ? (
                <TextButton label={`Go back to the ${money(previous.total)} cart`} onPress={() => switchTo(previous)} />
              ) : null}
            </>
          )}
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: colors.background },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center', backgroundColor: colors.background },
  content: { padding: spacing.lg, paddingTop: 8, gap: 20 },
  limit: { gap: 12, padding: spacing.md, borderRadius: radii.xl, backgroundColor: colors.surface },
  limitRefused: { backgroundColor: colors.errorSurface },
  limitTitle: { fontSize: 16, lineHeight: 20, fontWeight: '600', color: colors.text },
  limitAmount: { flexDirection: 'row', alignItems: 'baseline', gap: 6 },
  stat: { fontSize: 32, lineHeight: 36, fontWeight: '800', letterSpacing: -1, color: colors.text },
  statRefused: { color: colors.error },
  of: { fontSize: 17, lineHeight: 22, color: colors.textMuted },
  track: { height: 8, borderRadius: 4, backgroundColor: colors.hairline, overflow: 'hidden' },
  trackRefused: { backgroundColor: colors.errorTrack },
  fill: { height: 8, borderRadius: 4, backgroundColor: colors.primary },
  fillRefused: { backgroundColor: colors.error },
  limitMeta: { fontSize: 14, lineHeight: 20, color: colors.textBody },
  refusal: { fontSize: 14, lineHeight: 20, fontWeight: '500', color: colors.errorText },
  section: { fontSize: 20, lineHeight: 24, fontWeight: '700', color: colors.text, paddingBottom: 6 },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: colors.hairline,
  },
  thumb: { width: 36, height: 40, borderRadius: radii.sm },
  rowName: { flex: 1, fontSize: 15, lineHeight: 20, fontWeight: '500', color: colors.text },
  rowPrice: { width: 56, textAlign: 'right', fontSize: 15, lineHeight: 20, fontWeight: '600', color: colors.text },
  ownedNote: { fontSize: 14, lineHeight: 20, color: colors.textMuted, paddingTop: 10 },
  card: { flexDirection: 'row', alignItems: 'center', gap: 12 },
  visa: {
    width: 44,
    height: 30,
    borderRadius: 6,
    backgroundColor: '#1a1f71', // Visa card art
    alignItems: 'center',
    justifyContent: 'center',
  },
  visaText: { fontSize: 11, fontWeight: '800', fontStyle: 'italic', color: colors.onPrimary },
  cardText: { flex: 1, gap: 2 },
  cardLabel: { fontSize: 15, lineHeight: 20, fontWeight: '600', color: colors.text },
  muted: { fontSize: 13, lineHeight: 18, color: colors.textMuted },
  actions: { gap: 14 },
});
