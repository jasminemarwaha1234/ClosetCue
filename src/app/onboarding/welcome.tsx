import { Placeholder } from '@/components/Placeholder';

export default function WelcomeScreen() {
  return (
    <Placeholder
      description="What we read, what we keep, and the choice of how to share photos."
      links={[
        { label: 'Share your photos', href: '/onboarding/photos' },
      ]}
    />
  );
}
