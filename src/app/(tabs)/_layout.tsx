import { Tabs } from 'expo-router';

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
      <Tabs.Screen name="build" options={{ title: 'Build' }} />
      <Tabs.Screen name="style" options={{ title: 'Style' }} />
      <Tabs.Screen name="rate" options={{ title: 'Rate' }} />
      <Tabs.Screen name="trust" options={{ title: 'Trust' }} />
    </Tabs>
  );
}
