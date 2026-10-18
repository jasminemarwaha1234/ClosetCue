import { Stack } from 'expo-router';

export default function RootLayout() {
  return (
    <Stack>
      <Stack.Screen name="onboarding/welcome" options={{ title: 'Welcome' }} />
      <Stack.Screen name="onboarding/photos" options={{ headerShown: false }} />
      <Stack.Screen name="(tabs)" options={{ headerShown: false }} />
      <Stack.Screen name="pick-item" options={{ title: 'Pick an item', presentation: 'modal' }} />
      <Stack.Screen name="outfits" options={{ title: 'Outfits' }} />
      <Stack.Screen name="tryon/[outfitId]" options={{ title: 'Try it on' }} />
      <Stack.Screen name="checkout/index" options={{ title: 'Checkout' }} />
      <Stack.Screen name="checkout/receipt" options={{ title: 'Receipt' }} />
      <Stack.Screen name="fit/[orderId]" options={{ title: 'How did it fit?' }} />
    </Stack>
  );
}
