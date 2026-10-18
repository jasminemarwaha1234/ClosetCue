import { Redirect } from 'expo-router';

// Later: send people who already have a style profile to /build instead.
export default function Index() {
  return <Redirect href="/onboarding/welcome" />;
}
