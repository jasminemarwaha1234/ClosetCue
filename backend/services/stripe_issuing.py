# Stripe Issuing, in Stripe's sandbox: one virtual card per mandate, with the
# spending limit set on the card itself. PLAN.md section 8 has the design.
# Outline only: each function says what to build, then raises NotImplementedError.
#
# One-time setup in the Stripe dashboard (sandbox):
#   1. Turn on Issuing. If the dashboard asks for sales approval, use the fallback
#      in PLAN.md section 8 instead of this file.
#   2. Add funds to the sandbox Issuing balance. With a $0 balance, every simulated
#      purchase declines for insufficient funds, which looks like our limit working.
#   3. Create one cardholder (any name and US address) and put its ID in
#      backend/.env as STRIPE_CARDHOLDER_ID. Every agent card hangs off it.
#
# Env (backend/.env): STRIPE_SECRET_KEY (sk_test_...), STRIPE_CARDHOLDER_ID (ich_...).
# Amounts go to Stripe in cents; the API uses dollars, so convert at this boundary only.

from dataclasses import dataclass

# Merchant categories the card may be used at: the mandate's "apparel only".
# Check each name against https://docs.stripe.com/issuing/categories before using it.
APPAREL_CATEGORIES = [
    "family_clothing_stores",
    "mens_womens_clothing_stores",
    "womens_ready_to_wear_stores",
    "shoe_stores",
]


@dataclass
class IssuedCard:
    id: str  # ic_...
    brand: str  # check it's "Visa" (PLAN.md section 13)
    last4: str


@dataclass
class Authorization:
    id: str  # iauth_...; shown on the receipt
    approved: bool
    decline_reason: str | None  # Stripe's reason, e.g. "spending_controls"


def create_agent_card(limit_cents: int) -> IssuedCard:
    # POST /v1/issuing/cards with:
    #   cardholder = STRIPE_CARDHOLDER_ID, type = "virtual", currency = "usd", status = "active"
    #   spending_controls = {
    #     spending_limits: [{amount: limit_cents, interval: "all_time"}],
    #     allowed_categories: APPAREL_CATEGORIES,
    #   }
    # Never return or log the full card number; the agent only ever sees `last4`.
    raise NotImplementedError


def authorize(card_id: str, amount_cents: int) -> Authorization:
    # Simulates the store charging the card: POST /v1/test_helpers/issuing/authorizations
    # with card = card_id, amount = amount_cents, and merchant_data.category set to one of
    # APPAREL_CATEGORIES. Without that category, allowed_categories declines every purchase.
    # Stripe checks the card's spending controls itself: over the limit comes back with
    # approved = false and request_history[0].reason = "spending_controls".
    # If approved, capture it (POST /v1/test_helpers/issuing/authorizations/{id}/capture)
    # so the amount counts as spent on the card.
    raise NotImplementedError


def cancel_card(card_id: str) -> None:
    # POST /v1/issuing/cards/{card_id} with status = "canceled". Cancelling can't be undone.
    # Called after a purchase and when the mandate expires: Stripe's spending intervals
    # don't go below a day, so the 24-hour expiry is ours to enforce.
    raise NotImplementedError


def card_label(card: IssuedCard) -> str:
    # The CardRef.label the app shows, e.g. "Visa •••• 1234, agent card".
    raise NotImplementedError
