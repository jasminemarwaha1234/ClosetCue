import { Tabs } from 'expo-router';

import { BuildIcon, RateIcon, StyleIcon, TrustIcon } from '@/components/TabIcons';
import { colors } from '@/theme';

export default function TabsLayout() {
  return (
    <Tabs
      screenOptions={{
        headerShown: false,
        tabBarActiveTintColor: colors.primary,
        tabBarInactiveTintColor: colors.textMuted,
        tabBarStyle: { borderTopColor: colors.hairline },
      }}
    >
      <Tabs.Screen name="style" options={{ title: 'Style', tabBarIcon: StyleIcon }} />
      <Tabs.Screen name="build" options={{ title: 'Build', tabBarIcon: BuildIcon }} />
      <Tabs.Screen name="rate" options={{ title: 'Rate', tabBarIcon: RateIcon }} />
      <Tabs.Screen name="trust" options={{ title: 'Trust', tabBarIcon: TrustIcon }} />
    </Tabs>
  );
}
