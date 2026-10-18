import * as LocalAuthentication from 'expo-local-authentication';
import { Alert } from 'react-native';

// Asks the person to approve a payment with Face ID, Touch ID or the device passcode.
// Expo Go has no Face ID, so it falls back to the passcode. On a phone or simulator with
// nothing enrolled, it asks with a plain dialog instead, so the demo still works.
export async function confirmPayment(message: string): Promise<boolean> {
  const [hasHardware, enrolled] = await Promise.all([
    LocalAuthentication.hasHardwareAsync(),
    LocalAuthentication.isEnrolledAsync(),
  ]);
  if (hasHardware && enrolled) {
    const result = await LocalAuthentication.authenticateAsync({ promptMessage: message });
    return result.success;
  }
  return new Promise((resolve) =>
    Alert.alert(message, 'No Face ID or passcode is set up on this device.', [
      { text: 'Cancel', style: 'cancel', onPress: () => resolve(false) },
      { text: 'Pay', onPress: () => resolve(true) },
    ]),
  );
}
