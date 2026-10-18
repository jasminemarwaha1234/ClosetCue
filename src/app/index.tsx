import { Redirect } from 'expo-router';

// The app always opens on the welcome screen, which signs you in or, if you already are,
// lets you continue or switch accounts.
export default function Index() {
  return <Redirect href="/onboarding/welcome" />;
}
