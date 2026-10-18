# Checkout under a spending mandate. PLAN.md section 8 has the design, and
# backend/services/stripe_issuing.py does the Stripe calls.
# Outline only: each route says what to build, then answers 501 Not Implemented.
#
# Where mandates live: Supabase's `mandates` table (id, user_id, limit, spent,
# expires_at, card_id, card_label). A dict in memory works until Supabase is wired up,
# but loses every mandate when the server restarts.
#
# Fallback if Stripe Issuing isn't available (PLAN.md section 8): skip the Stripe calls,
# use the fixed label "Visa •••• 4242", and return Receipt.authorization_id = None so
# the app labels the payment as simulated.

from fastapi import APIRouter, HTTPException

from backend.schemas import CartRequest, CartVerdict, Mandate, MandateRequest, Receipt

router = APIRouter()


@router.post("/checkout/mandate")
async def create_mandate(req: MandateRequest) -> Mandate:
    # 1. stripe_issuing.create_agent_card(limit in cents).
    # 2. Store the mandate with expires_at = now + req.hours and spent = 0.
    # 3. Return it with card = CardRef(label=stripe_issuing.card_label(card)).
    raise HTTPException(501, "Not implemented yet")


@router.post("/checkout/cart")
async def check_cart(req: CartRequest) -> CartVerdict:
    # Our own check, before Face ID. It never calls Stripe, so it answers fast.
    # 1. Load the mandate. Missing or past expires_at: refused, reason "expired".
    # 2. Look up each item_id in the catalog. Total from catalog prices, never from the app.
    #    An item that isn't apparel: refused, reason "not_apparel".
    # 3. total > limit - spent: refused, reason "over_limit", with a message naming the
    #    amount over and `suggestion` set to the closest outfit that fits.
    # 4. Otherwise allowed, with remaining = limit - spent - total.
    raise HTTPException(501, "Not implemented yet")


@router.post("/checkout/confirm")
async def confirm(req: CartRequest) -> Receipt:
    # After Face ID.
    # 1. Run the same check as /checkout/cart. If it refuses now, 409.
    # 2. stripe_issuing.authorize(card_id, total in cents). If Stripe declines, 409 with
    #    its reason: the card's own limit caught something our check missed.
    # 3. Add total to the mandate's spent, then stripe_issuing.cancel_card(card_id).
    # 4. Return the receipt with the authorization's id as authorization_id.
    raise HTTPException(501, "Not implemented yet")
