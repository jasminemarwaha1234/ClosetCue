import type { ReactNode } from 'react';
import * as WebBrowser from 'expo-web-browser';
import {
  ActivityIndicator,
  Image,
  Pressable,
  StyleSheet,
  Text,
  View,
  type StyleProp,
  type ViewStyle,
} from 'react-native';

import { colors, radii, swatches, type } from '@/theme';

// Building blocks shared by the screens designed in Paper ("As If / …" frames).

export function Header({ eyebrow, title, lead }: { eyebrow: string; title: string; lead?: string }) {
  return (
    <View style={styles.header}>
      <Text style={styles.eyebrow}>{eyebrow.toUpperCase()}</Text>
      <Text style={styles.title}>{title}</Text>
      {lead ? <Text style={styles.lead}>{lead}</Text> : null}
    </View>
  );
}

export function SectionTitle({ children }: { children: ReactNode }) {
  return <Text style={styles.section}>{children}</Text>;
}

type ButtonProps = {
  label: string;
  onPress: () => void;
  icon?: ReactNode;
  loading?: boolean;
  disabled?: boolean;
  style?: StyleProp<ViewStyle>;
};

export function PrimaryButton({ label, onPress, icon, loading, disabled, style }: ButtonProps) {
  return (
    <Pressable
      onPress={onPress}
      disabled={disabled || loading}
      style={({ pressed }) => [
        styles.primary,
        (pressed || disabled) && styles.dim,
        style,
      ]}
    >
      {loading ? (
        <ActivityIndicator color={colors.onPrimary} />
      ) : (
        <>
          {icon}
          <Text style={styles.primaryText}>{label}</Text>
        </>
      )}
    </Pressable>
  );
}

export function OutlineButton({ label, onPress, icon, loading, disabled, style }: ButtonProps) {
  return (
    <Pressable
      onPress={onPress}
      disabled={disabled || loading}
      style={({ pressed }) => [styles.outline, (pressed || disabled) && styles.dim, style]}
    >
      {loading ? (
        <ActivityIndicator color={colors.primary} />
      ) : (
        <>
          {icon}
          <Text style={styles.linkText}>{label}</Text>
        </>
      )}
    </Pressable>
  );
}

export function TextButton({ label, onPress, style }: { label: string; onPress: () => void; style?: StyleProp<ViewStyle> }) {
  return (
    <Pressable onPress={onPress} hitSlop={8} style={({ pressed }) => [styles.textButton, pressed && styles.dim, style]}>
      <Text style={styles.linkText}>{label}</Text>
    </Pressable>
  );
}

// Opens an item's real product page in an in-app browser. Hidden when there's no URL.
export function RetailerLink({ url, label = 'View at retailer' }: { url: string; label?: string }) {
  if (!url) return null;
  return (
    <Pressable
      onPress={() => WebBrowser.openBrowserAsync(url)}
      hitSlop={6}
      accessibilityRole="link"
      accessibilityLabel="View at retailer"
      style={({ pressed }) => pressed && styles.dim}
    >
      <Text style={styles.retailer}>{label} ↗</Text>
    </Pressable>
  );
}

export function Chip({
  label,
  selected,
  onPress,
  variant = 'soft',
}: {
  label: string;
  selected?: boolean;
  onPress?: () => void;
  variant?: 'soft' | 'outline';
}) {
  const outline = variant === 'outline';
  return (
    <Pressable
      onPress={onPress}
      style={[
        styles.chip,
        outline ? styles.chipOutline : styles.chipSoft,
        selected && (outline ? styles.chipInk : styles.chipSelected),
      ]}
    >
      <Text
        style={[
          styles.chipText,
          outline && styles.chipOutlineText,
          selected && styles.chipSelectedText,
        ]}
      >
        {label}
      </Text>
    </Pressable>
  );
}

// A two-way toggle, like "On you / Flat lay".
export function Segmented<T extends string>({
  options,
  value,
  onChange,
}: {
  options: { value: T; label: string }[];
  value: T;
  onChange: (v: T) => void;
}) {
  return (
    <View style={styles.segmented}>
      {options.map((o) => (
        <Pressable
          key={o.value}
          onPress={() => onChange(o.value)}
          style={[styles.segment, value === o.value && styles.segmentOn]}
        >
          <Text style={[styles.segmentText, value === o.value && styles.segmentTextOn]}>{o.label}</Text>
        </Pressable>
      ))}
    </View>
  );
}

// An item's photo, or a block of its first color when there's no image.
// Shopify's CDN resizes on request, so tiles don't download full-size product photos.
const thumbnail = (url: string) =>
  url.includes('cdn.shopify.com') ? `${url}${url.includes('?') ? '&' : '?'}width=400` : url;

export function PieceImage({
  image,
  colorName,
  style,
  dashed,
}: {
  image?: string;
  colorName?: string;
  style?: StyleProp<ViewStyle>;
  dashed?: boolean;
}) {
  const bg = (colorName && swatches[colorName.toLowerCase()]) || colors.surfaceMuted;
  const light = bg === '#ffffff';
  return (
    <View
      style={[
        styles.piece,
        { backgroundColor: bg },
        light && styles.pieceLight,
        dashed && styles.pieceDashed,
        style,
      ]}
    >
      {image ? <Image source={{ uri: thumbnail(image) }} style={StyleSheet.absoluteFill} resizeMode="cover" /> : null}
    </View>
  );
}

export const money = (n: number) => `$${Math.round(n)}`;

const styles = StyleSheet.create({
  header: { gap: 8 },
  eyebrow: { ...type.eyebrow, lineHeight: 18, color: colors.primary },
  title: { ...type.title, color: colors.text },
  lead: { ...type.lead, color: colors.textMuted },
  section: { ...type.section, color: colors.text },

  primary: {
    height: 56,
    borderRadius: radii.pill,
    backgroundColor: colors.primary,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 10,
    paddingHorizontal: 20,
  },
  primaryText: { ...type.button, lineHeight: 22, color: colors.onPrimary },
  outline: {
    height: 52,
    borderRadius: 26,
    borderWidth: 1.5,
    borderColor: colors.primary,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    paddingHorizontal: 20,
  },
  linkText: { fontSize: 16, lineHeight: 20, fontWeight: '600', color: colors.onPrimarySoft },
  retailer: { fontSize: 13, lineHeight: 18, fontWeight: '600', color: colors.primary },
  textButton: { minHeight: 24, alignItems: 'center', justifyContent: 'center' },
  dim: { opacity: 0.6 },

  chip: { height: 40, paddingHorizontal: 16, borderRadius: 20, justifyContent: 'center' },
  chipSoft: { backgroundColor: colors.surface },
  chipSelected: { backgroundColor: colors.primary },
  chipOutline: { height: 36, paddingHorizontal: 14, borderWidth: 1, borderColor: colors.hairline },
  chipInk: { backgroundColor: colors.ink, borderColor: colors.ink },
  chipText: { fontSize: 15, lineHeight: 18, fontWeight: '600', color: colors.onPrimarySoft },
  chipOutlineText: { fontSize: 14, color: colors.textBody },
  chipSelectedText: { color: colors.onPrimary },

  segmented: { flexDirection: 'row', padding: 4, borderRadius: 24, backgroundColor: colors.surface },
  segment: { flex: 1, height: 40, borderRadius: 20, alignItems: 'center', justifyContent: 'center' },
  segmentOn: {
    backgroundColor: colors.background,
    shadowColor: colors.text,
    shadowOpacity: 0.08,
    shadowRadius: 3,
    shadowOffset: { width: 0, height: 1 },
    elevation: 1,
  },
  segmentText: { fontSize: 15, lineHeight: 18, fontWeight: '600', color: colors.textMuted },
  segmentTextOn: { color: colors.text },

  piece: { borderRadius: radii.lg, overflow: 'hidden' },
  pieceLight: { borderWidth: 1, borderColor: colors.hairline },
  pieceDashed: { borderWidth: 1.5, borderStyle: 'dashed', borderColor: colors.dashed },
});
