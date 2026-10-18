# One-time Stripe sandbox setup for checkout (PLAN.md section 8). Run from the repo root:
#   python -m backend.stripe_setup
#
# Needs STRIPE_SECRET_KEY=sk_test_... in backend/.env and Issuing turned on in the Stripe
# dashboard (sandbox). It:
#   1. Adds $1,000 of test money to the Issuing balance. With $0, every simulated purchase
#      declines for insufficient funds, which would look like our limit working.
#   2. Creates the one cardholder every agent card hangs off, unless STRIPE_CARDHOLDER_ID is set.
#   3. Issues one test card and checks it's a Visa, then cancels it.
# Then put the printed STRIPE_CARDHOLDER_ID in backend/.env and restart the backend.

import os
import sys
import time

from backend.services import stripe_issuing


def main() -> None:
    try:
        client = stripe_issuing._client()
    except RuntimeError as e:
        sys.exit(str(e))

    client.v1.topups.create(
        params={
            "amount": 100_000,
            "currency": "usd",
            "destination_balance": "issuing",
            "description": "ClosetCue sandbox funds",
        }
    )
    print("Added $1,000 of test funds to the Issuing balance.")

    cardholder_id = os.environ.get("STRIPE_CARDHOLDER_ID")
    if not cardholder_id:
        holder = client.v1.issuing.cardholders.create(
            params={
                "type": "individual",
                "name": "ClosetCue Agent",
                "individual": {
                    "first_name": "ClosetCue",
                    "last_name": "Agent",
                    # Stripe won't issue cards until the cardholder terms are accepted.
                    "card_issuing": {"user_terms_acceptance": {"date": int(time.time()), "ip": "127.0.0.1"}},
                },
                "billing": {
                    "address": {
                        "line1": "123 Main St",
                        "city": "Los Angeles",
                        "state": "CA",
                        "postal_code": "90095",
                        "country": "US",
                    }
                },
            }
        )
        cardholder_id = holder.id
        os.environ["STRIPE_CARDHOLDER_ID"] = cardholder_id
        print(f"Created the cardholder. Add this line to backend/.env:\n  STRIPE_CARDHOLDER_ID={cardholder_id}")
    else:
        print("Using the cardholder already in backend/.env.")

    card = stripe_issuing.create_agent_card(100)
    print(f"Test card issued: {card.brand} •••• {card.last4}")
    stripe_issuing.cancel_card(card.id)
    if card.brand != "Visa":
        print("Note: the card isn't a Visa. Checkout still works, but the Visa-track story changes.")


if __name__ == "__main__":
    main()
