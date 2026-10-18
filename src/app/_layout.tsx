import { Stack } from 'expo-router';

import { SessionProvider } from '@/lib/session';
import { colors } from '@/theme';

export default function RootLayout() {
  return (
    <SessionProvider>
      <Stack
        screenOptions={{
          headerShadowVisible: false,
          headerBackButtonDisplayMode: 'minimal',
          headerTintColor: colors.text,
          headerTitleStyle: { fontSize: 14, fontWeight: '500', color: colors.textMuted },
          headerStyle: { backgroundColor: colors.background },
        }}
      >
        <Stack.Screen name="onboarding/welcome" options={{ title: 'Welcome' }} />
        <Stack.Screen name="onboarding/photos" options={{ headerShown: false }} />
        <Stack.Screen name="(tabs)" options={{ headerShown: false }} />
        <Stack.Screen name="pick-item" options={{ headerShown: false, presentation: 'modal' }} />
        <Stack.Screen name="outfits" options={{ title: '' }} />
        <Stack.Screen name="tryon/[outfitId]" options={{ title: '' }} />
        <Stack.Screen name="checkout/index" options={{ title: '' }} />
        <Stack.Screen name="checkout/receipt" options={{ headerShown: false }} />
        <Stack.Screen name="fit/[orderId]" options={{ title: 'How did it fit?' }} />
      </Stack>
    </SessionProvider>
  );
}
