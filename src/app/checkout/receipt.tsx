import { Placeholder } from '@/components/Placeholder';

export default function ReceiptScreen() {
  return (
    <Placeholder
      description="What was bought, what it cost, what's left of the spending limit, and the Stripe authorization ID (or a 'simulated payment' label when there is none)."
      links={[
        { label: 'How did it fit?', href: '/fit/demo' },
      ]}
    />
  );
}
