import { useEffect, useState } from 'react';
import { Redirect, type Href } from 'expo-router';
import { ActivityIndicator, View } from 'react-native';

import { hasProfile } from '@/lib/onboarding';
import { getSession } from '@/lib/supabase';
import { colors } from '@/theme';

// Where the app opens: the welcome screen when nobody is signed in, the photo scan for an
// account without a profile yet, and Build for everyone who has finished onboarding.
export default function Index() {
  const [href, setHref] = useState<Href | null>(null);

  useEffect(() => {
    getSession()
      .then(async (session) => {
        if (!session) return '/onboarding/welcome' as const;
        return (await hasProfile(session.user.id)) ? ('/build' as const) : ('/onboarding/photos' as const);
      })
      .catch(() => '/onboarding/welcome' as const)
      .then(setHref);
  }, []);

  if (!href) {
    return (
      <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center', backgroundColor: colors.background }}>
        <ActivityIndicator color={colors.primary} />
      </View>
    );
  }
  return <Redirect href={href} />;
}
