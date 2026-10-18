import { ActivityIndicator, Alert, Modal, Pressable, StyleSheet, Text, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { AppleLogo } from '@/components/logos';
import { money } from '@/components/ui';
import { PAY_METHODS, type PayMethodId } from '@/lib/payment';
import { brands, colors, radii, spacing } from '@/theme';

// The method's little card-shaped mark, shared with the checkout's "Pay with" row.
export function PayMark({ id }: { id: PayMethodId }) {
  if (id === 'apple_pay') {
    return (
      <View style={[styles.mark, { backgroundColor: brands.applePay }]}>
        <AppleLogo size={13} />
        <Text style={styles.markApple}>Pay</Text>
      </View>
    );
  }
  if (id === 'card') {
    return (
      <View style={[styles.mark, { backgroundColor: brands.visa }]}>
        <Text style={styles.markVisa}>VISA</Text>
      </View>
    );
  }
  return (
    <View style={[styles.mark, { backgroundColor: brands.paypal }]}>
      <Text style={styles.markPaypal}>PayPal</Text>
    </View>
  );
}

// "Pay with": pick how to pay, then pay. Designed in Paper ("As If / Checkout – pay with").
// Simulated for the demo (src/lib/payment.ts); the limit check and refusal stay real.
export function PaySheet({
  visible,
  total,
  limit,
  method,
  onChange,
  onPay,
  onClose,
  paying,
}: {
  visible: boolean;
  total: number;
  limit: number;
  method: PayMethodId;
  onChange: (id: PayMethodId) => void;
  onPay: () => void;
  onClose: () => void;
  paying: boolean;
}) {
  const insets = useSafeAreaInsets();
  const apple = method === 'apple_pay';

  return (
    <Modal visible={visible} transparent animationType="slide" onRequestClose={onClose}>
      <Pressable style={styles.scrim} onPress={onClose} accessibilityLabel="Close" />
      <View style={[styles.sheet, { paddingBottom: Math.max(insets.bottom, spacing.lg) }]}>
        <View style={styles.grabber} />
        <View style={styles.header}>
          <Text style={styles.title}>Pay with</Text>
          <Text style={styles.title}>{money(total)}</Text>
        </View>

        <View style={styles.methods}>
          {PAY_METHODS.map((m) => {
            const selected = m.id === method;
            return (
              <Pressable
                key={m.id}
                onPress={() => onChange(m.id)}
                style={[styles.row, selected && styles.rowSelected]}
                accessibilityRole="radio"
                accessibilityState={{ selected }}
              >
                <PayMark id={m.id} />
                <View style={styles.rowText}>
                  <Text style={styles.rowLabel}>{m.label}</Text>
                  <Text style={styles.rowDetail}>{m.detail}</Text>
                </View>
                <View style={[styles.radio, selected && styles.radioOn]}>
                  {selected ? <Text style={styles.check}>✓</Text> : null}
                </View>
              </Pressable>
            );
          })}
          <Pressable
            style={styles.add}
            onPress={() => Alert.alert('Add a card', "Adding cards isn't part of the demo. Pick one of the saved ones.")}
          >
            <View style={styles.addMark}>
              <Text style={styles.addPlus}>+</Text>
            </View>
            <Text style={styles.addText}>Add a card</Text>
          </Pressable>
        </View>

        <View style={styles.footer}>
          <Pressable
            onPress={onPay}
            disabled={paying}
            style={({ pressed }) => [styles.pay, apple && styles.payApple, (pressed || paying) && styles.dim]}
          >
            {paying ? (
              <ActivityIndicator color={colors.onPrimary} />
            ) : apple ? (
              <>
                <Text style={styles.payText}>Pay {money(total)} with</Text>
                <AppleLogo size={17} />
                <Text style={styles.payText}>Pay</Text>
              </>
            ) : (
              <Text style={styles.payText}>Pay {money(total)}</Text>
            )}
          </Pressable>
          <Text style={styles.note}>
            Demo: nothing is charged. The agent's card, capped at your {money(limit)} limit, pays the store.
          </Text>
        </View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  scrim: { flex: 1, backgroundColor: colors.scrim },
  sheet: {
    gap: 18,
    paddingTop: 12,
    paddingHorizontal: spacing.lg,
    borderTopLeftRadius: 28,
    borderTopRightRadius: 28,
    backgroundColor: colors.background,
  },
  grabber: { alignSelf: 'center', width: 40, height: 5, borderRadius: 3, backgroundColor: colors.hairline },
  header: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'baseline' },
  title: { fontSize: 24, lineHeight: 28, fontWeight: '800', letterSpacing: -0.72, color: colors.text },
  methods: { gap: 8 },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 14,
    paddingVertical: 14,
    paddingHorizontal: spacing.md,
    borderRadius: 16,
    borderWidth: 1.5,
    borderColor: colors.hairline,
  },
  rowSelected: { borderWidth: 2, borderColor: colors.primary, backgroundColor: colors.surface },
  rowText: { flex: 1, gap: 2 },
  rowLabel: { fontSize: 16, lineHeight: 20, fontWeight: '600', color: colors.text },
  rowDetail: { fontSize: 13, lineHeight: 18, color: colors.textMuted },
  radio: {
    width: 22,
    height: 22,
    borderRadius: 11,
    borderWidth: 1.5,
    borderColor: colors.dashed,
    alignItems: 'center',
    justifyContent: 'center',
  },
  radioOn: { borderWidth: 0, backgroundColor: colors.primary },
  check: { fontSize: 12, lineHeight: 14, fontWeight: '800', color: colors.onPrimary },
  mark: {
    width: 48,
    height: 32,
    borderRadius: 6,
    flexDirection: 'row',
    gap: 2,
    alignItems: 'center',
    justifyContent: 'center',
  },
  markApple: { fontSize: 12, lineHeight: 14, fontWeight: '600', color: colors.onPrimary },
  markVisa: { fontSize: 12, lineHeight: 14, fontWeight: '800', fontStyle: 'italic', color: colors.onPrimary },
  markPaypal: { fontSize: 11, lineHeight: 14, fontWeight: '800', fontStyle: 'italic', color: brands.paypalText },
  add: { flexDirection: 'row', alignItems: 'center', gap: 14, paddingVertical: 14, paddingHorizontal: spacing.md },
  addMark: {
    width: 48,
    height: 32,
    borderRadius: 6,
    borderWidth: 1.5,
    borderStyle: 'dashed',
    borderColor: colors.dashed,
    alignItems: 'center',
    justifyContent: 'center',
  },
  addPlus: { fontSize: 18, lineHeight: 20, fontWeight: '600', color: colors.primary },
  addText: { fontSize: 16, lineHeight: 20, fontWeight: '600', color: colors.onPrimarySoft },
  footer: { gap: 12 },
  pay: {
    flexDirection: 'row',
    gap: 8,
    height: 56,
    borderRadius: radii.pill,
    backgroundColor: colors.primary,
    alignItems: 'center',
    justifyContent: 'center',
  },
  payApple: { backgroundColor: brands.applePay },
  payText: { fontSize: 17, lineHeight: 22, fontWeight: '600', color: colors.onPrimary },
  note: { fontSize: 13, lineHeight: 18, color: colors.textMuted, textAlign: 'center', paddingHorizontal: 12 },
  dim: { opacity: 0.6 },
});
