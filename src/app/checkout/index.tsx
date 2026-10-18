import { Placeholder } from '@/components/Placeholder';

export default function CheckoutScreen() {
  return (
    <Placeholder
      description="The cart, the spending limit, the agent's spending-limited card (Stripe Issuing, sandbox), confirm. Carts over the limit are refused with the reason shown."
      links={[
        { label: 'Confirm', href: '/checkout/receipt' },
      ]}
    />
  );
}
