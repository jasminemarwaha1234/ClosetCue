import Constants, { ExecutionEnvironment } from 'expo-constants';
import * as LocalAuthentication from 'expo-local-authentication';
import { Alert } from 'react-native';

const REFUSED: LocalAuthentication.LocalAuthenticationError[] = [
  'user_cancel',
  'system_cancel',
  'app_cancel',
  'authentication_failed',
  'lockout',
];

// Asks the person to approve a payment. No card is entered: this only checks it's really them.
// Face ID or Touch ID when it's available (a development build). Expo Go has no Face ID, and
// we don't want the phone's passcode screen there, so it asks with an in-app dialog instead.
export async function confirmPayment(message: string): Promise<boolean> {
  // Expo Go can't use Face ID and shows the phone's passcode screen instead, so skip it there.
  const inExpoGo = Constants.executionEnvironment === ExecutionEnvironment.StoreClient;
  const [hasHardware, enrolled] = inExpoGo ? [false, false] : await Promise.all([
    LocalAuthentication.hasHardwareAsync(),
    LocalAuthentication.isEnrolledAsync(),
  ]);
  if (hasHardware && enrolled) {
    const result = await LocalAuthentication.authenticateAsync({
      promptMessage: message,
      disableDeviceFallback: true,
      fallbackLabel: '',
    });
    if (result.success) return true;
    // Cancelled, or the face didn't match: don't pay. Anything else means Face ID can't run here.
    if (REFUSED.includes(result.error)) return false;
  }
  return new Promise((resolve) =>
    Alert.alert(message, 'This is a test payment. No real card is used and no money moves.', [
      { text: 'Cancel', style: 'cancel', onPress: () => resolve(false) },
      { text: 'Pay', onPress: () => resolve(true) },
    ]),
  );
}
