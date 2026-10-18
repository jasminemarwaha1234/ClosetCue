import { Placeholder } from '@/components/Placeholder';

export default function StyleScreen() {
  return (
    <Placeholder
      description="Your style profile as a short, editable summary, with your photos grouped into looks."
      links={[
        { label: 'Build an outfit', href: '/build' },
      ]}
    />
  );
}
