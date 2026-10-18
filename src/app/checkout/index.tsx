import { Placeholder } from '@/components/Placeholder';

export default function CheckoutScreen() {
  return (
    <Placeholder
      description="The cart, the spending limit, the tokenized card, confirm. Carts over the limit are refused with the reason shown."
      links={[
        { label: 'Confirm', href: '/checkout/receipt' },
      ]}
    />
  );
}
