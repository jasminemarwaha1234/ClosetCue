import * as Sentry from '@sentry/react-native';
import { isRunningInExpoGo } from 'expo';

// Sentry for the app. The backend has its own setup with sentry-sdk (backend/main.py).
//
// Plan (PLAN.md, the Sentry row in the challenges table): "Best Use of Sentry" needs
// at least two products beyond error monitoring. We aim for:
//   1. Tracing: one trace per user action, from the screen through the backend to Veri
//      and Gemini. The app starts the trace, and fetch calls carry the `sentry-trace` and
//      `baggage` headers so the backend's spans join it (see tracePropagationTargets).
//   2. Logs: Sentry.logger.info/warn/error for events worth reading later
//      (scan finished, outfit rejected by the guard, checkout confirmed).
//   3. AI monitoring: on the backend, around the Veri and Gemini calls.
// Session Replay needs a development build, and the demo runs in Expo Go, so it's off.

// Tracks screen changes as spans. Registered with Expo Router's navigation container
// in src/app/_layout.tsx (see registerNavigation below).
const navigationIntegration = Sentry.reactNavigationIntegration({
  // Time to initial display needs native code that Expo Go doesn't have.
  enableTimeToInitialDisplay: !isRunningInExpoGo(),
});

// Call once, at the top of src/app/_layout.tsx, outside the component.
// Then wrap the root layout: `export default Sentry.wrap(RootLayout);`
export function initSentry() {
  const dsn = process.env.EXPO_PUBLIC_SENTRY_DSN;
  if (!dsn) return; // no DSN in .env: Sentry stays off

  Sentry.init({
    dsn,
    // Send every trace: a hackathon demo has little traffic, and we want all of it.
    tracesSampleRate: 1.0,
    enableLogs: true,
    integrations: [navigationIntegration],
    // Attach trace headers only to our own backend, not to Supabase or other hosts.
    tracePropagationTargets: [process.env.EXPO_PUBLIC_API_BASE_URL ?? 'localhost'],
  });
}

// In src/app/_layout.tsx:
//   const ref = useNavigationContainerRef(); // from expo-router
//   useEffect(() => { if (ref) registerNavigation(ref); }, [ref]);
export function registerNavigation(ref: unknown) {
  navigationIntegration.registerNavigationContainer(ref);
}

// TODO: once Supabase anonymous sign-in exists (src/lib/supabase.ts), call
// Sentry.setUser({ id }) with the anonymous user ID so traces group by user.
// Only the ID: no email or photos.
