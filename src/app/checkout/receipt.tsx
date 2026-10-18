import { Placeholder } from '@/components/Placeholder';

export default function ReceiptScreen() {
  return (
    <Placeholder
      description="What was bought, what it cost, and what's left of the spending limit."
      links={[
        { label: 'How did it fit?', href: '/fit/demo' },
      ]}
    />
  );
}
