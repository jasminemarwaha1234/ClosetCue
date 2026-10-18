import { Placeholder } from '@/components/Placeholder';

export default function TryOnScreen() {
  return (
    <Placeholder
      description="Your photo wearing the outfit, plus a flat-lay view."
      links={[
        { label: 'Check out', href: '/checkout' },
      ]}
    />
  );
}
