import { Link, type Href } from 'expo-router';
import { ScrollView, StyleSheet, Text } from 'react-native';

import { colors } from '@/theme';

// Stands in for a screen that isn't built yet. Delete it once every route is real.
export function Placeholder({
  description,
  links = [],
}: {
  description: string;
  links?: { label: string; href: Href }[];
}) {
  return (
    <ScrollView contentContainerStyle={styles.content}>
      <Text style={styles.description}>{description}</Text>
      {links.map((l) => (
        <Link key={l.label} href={l.href} style={styles.link}>
          {l.label}
        </Link>
      ))}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  content: { padding: 24, gap: 16 },
  description: { fontSize: 15, color: colors.textMuted },
  link: { color: colors.primary, fontWeight: '600', fontSize: 16 },
});
