// The payment methods in the checkout's "Pay with" picker. Simulated for the demo: picking one
// changes the labels and the Face ID prompt, and nothing is charged. The real money path is the
// agent's spending-limited card (PLAN.md section 8), which the mandate and Stripe enforce.

export type PayMethodId = 'apple_pay' | 'card' | 'paypal';

export type PayMethod = { id: PayMethodId; label: string; detail: string };

export const PAY_METHODS: PayMethod[] = [
  { id: 'apple_pay', label: 'Apple Pay', detail: 'Confirm with Face ID' },
  { id: 'card', label: 'Visa •••• 4242', detail: 'Expires 12/29' },
  { id: 'paypal', label: 'PayPal', detail: 'you@example.com' },
];

export const payMethod = (id: PayMethodId) => PAY_METHODS.find((m) => m.id === id) ?? PAY_METHODS[0];
