import { Placeholder } from '@/components/Placeholder';

export default function BuildScreen() {
  return (
    <Placeholder
      description="Pick an anchor item, set a budget and an occasion."
      links={[
        { label: 'Pick an anchor item', href: '/pick-item' },
        { label: 'Get outfits', href: '/outfits' },
      ]}
    />
  );
}
