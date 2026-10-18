# Stripe Issuing, in Stripe's sandbox: one virtual Visa card per mandate, with the
# spending limit set on the card itself. PLAN.md section 8 has the design.
#
# One-time setup (sandbox): turn on Issuing in the Stripe dashboard, then run
#   python -m backend.stripe_setup
# which funds the sandbox Issuing balance and creates the one cardholder every agent card
# hangs off, and prints the STRIPE_CARDHOLDER_ID to put in backend/.env.
#
# Env (backend/.env): STRIPE_SECRET_KEY (sk_test_...), STRIPE_CARDHOLDER_ID (ich_...).
# Without both, `configured()` is False and checkout uses the fallback: the mandate is
# enforced in our code only and the payment is labeled as simulated.
# Amounts go to Stripe in cents; the API uses dollars, so convert at this boundary only.

import os
from dataclasses import dataclass
from functools import cache
from pathlib import Path

import stripe
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

# Merchant categories the card may be used at: the mandate's "apparel only".
APPAREL_CATEGORIES = [
    "family_clothing_stores",
    "mens_womens_clothing_stores",
    "womens_ready_to_wear_stores",
    "shoe_stores",
]
# The category simulated purchases come from, so allowed_categories lets them through.
STORE_CATEGORY = "family_clothing_stores"


@dataclass
class IssuedCard:
    id: str  # ic_...
    brand: str  # "Visa"
    last4: str


@dataclass
class Authorization:
    id: str  # iauth_...; shown on the receipt
    approved: bool
    decline_reason: str | None  # Stripe's reason, e.g. "spending_controls"


def configured() -> bool:
    key = os.environ.get("STRIPE_SECRET_KEY", "")
    return key.startswith("sk_test_") and bool(os.environ.get("STRIPE_CARDHOLDER_ID"))


@cache
def _client() -> stripe.StripeClient:
    key = os.environ.get("STRIPE_SECRET_KEY", "")
    if not key.startswith("sk_test_"):
        # Sandbox only: a live key would issue real cards.
        raise RuntimeError("STRIPE_SECRET_KEY must be a test key (sk_test_...)")
    return stripe.StripeClient(key)


def create_agent_card(limit_cents: int) -> IssuedCard:
    """A virtual card that Stripe itself won't let spend past `limit_cents`, apparel only."""
    card = _client().v1.issuing.cards.create(
        params={
            "cardholder": os.environ["STRIPE_CARDHOLDER_ID"],
            "type": "virtual",
            "currency": "usd",
            "status": "active",
            "spending_controls": {
                "spending_limits": [{"amount": limit_cents, "interval": "all_time"}],
                "allowed_categories": APPAREL_CATEGORIES,
            },
        }
    )
    # Never return or log the full card number; the agent only ever sees `last4`.
    return IssuedCard(id=card.id, brand=card.brand, last4=card.last4)


def authorize(card_id: str, amount_cents: int) -> Authorization:
    """Simulates the store charging the card. Stripe checks the card's spending controls
    itself, so over the limit comes back declined with reason "spending_controls"."""
    client = _client()
    auth = client.v1.test_helpers.issuing.authorizations.create(
        params={
            "card": card_id,
            "amount": amount_cents,
            "currency": "usd",
            "merchant_data": {"category": STORE_CATEGORY, "name": "ClosetCue demo store"},
        }
    )
    if not auth.approved:
        history = auth.request_history or []
        return Authorization(id=auth.id, approved=False, decline_reason=history[0].reason if history else None)
    # Capture it so the amount counts as spent on the card.
    client.v1.test_helpers.issuing.authorizations.capture(auth.id)
    return Authorization(id=auth.id, approved=True, decline_reason=None)


def cancel_card(card_id: str) -> None:
    """Cancelling can't be undone. Called after a purchase and when the mandate expires:
    Stripe's spending intervals don't go below a day, so the 24-hour expiry is ours."""
    _client().v1.issuing.cards.update(card_id, params={"status": "canceled"})


def card_label(card: IssuedCard) -> str:
    """The CardRef.label the app shows, e.g. "Visa •••• 1234, agent card"."""
    return f"{card.brand} •••• {card.last4}, agent card"
