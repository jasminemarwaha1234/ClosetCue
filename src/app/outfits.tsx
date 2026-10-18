import { Placeholder } from '@/components/Placeholder';

export default function OutfitsScreen() {
  return (
    <Placeholder
      description="2-3 outfit cards with total price and reasons. Swap any piece."
      links={[
        { label: 'Try it on', href: '/tryon/demo' },
        { label: 'Check out', href: '/checkout' },
      ]}
    />
  );
}
