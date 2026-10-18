# Checkout under a spending mandate. PLAN.md section 8 has the design, and
# backend/services/stripe_issuing.py does the Stripe calls.
#
# The limit is enforced twice: here, before Face ID, from catalog prices; and by Stripe on the
# agent's virtual Visa card, whose own spending limit is the mandate's. Mandates live in
# Supabase's `mandates` table, one per user.
#
# Fallback when Stripe isn't set up (stripe_issuing.configured() is False): no card is issued,
# the label is the fixed "Visa •••• 4242, agent card", and the receipt's authorization_id is
# None, so the app labels the payment as simulated.

import asyncio
import logging
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException

from backend.schemas import (
    CardRef,
    CartAllowed,
    CartRefused,
    CartRequest,
    CatalogItem,
    Mandate,
    MandateRequest,
    Outfit,
    Receipt,
)
from backend.services import catalog, stripe_issuing, supabase

router = APIRouter()
log = logging.getLogger(__name__)

FALLBACK_LABEL = "Visa •••• 4242, agent card"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _cents(dollars: float) -> int:
    return round(dollars * 100)


def _mandate(row: dict) -> Mandate:
    return Mandate(
        id=row["id"],
        limit=float(row["limit"]),
        spent=float(row["spent"]),
        category="apparel",
        expires_at=row["expires_at"],
        card=CardRef(label=row["card_label"]),
    )


def _total(items: list[CatalogItem]) -> float:
    return round(sum(i.price for i in items), 2)


def _closest_under(cart: list[CatalogItem], budget: float) -> Outfit | None:
    """The closest cart under `budget`: the priciest piece becomes a cheaper one from the
    same slot and department, or is dropped, until it fits. At least one piece stays."""
    pool = list(catalog.items().values())
    cart = list(cart)
    while _total(cart) > budget and cart:
        priciest = max(cart, key=lambda i: i.price)
        over = _total(cart) - budget
        cheaper = sorted(
            (
                c
                for c in pool
                if c.slot == priciest.slot
                and c.price < priciest.price
                and c.department in (priciest.department, "unisex")
                and c not in cart
            ),
            key=lambda c: -c.price,
        )
        replacement = next((c for c in cheaper if priciest.price - c.price >= over), cheaper[-1] if cheaper else None)
        cart.remove(priciest)
        if replacement:
            cart.append(replacement)
    if not cart or _total(cart) > budget:
        return None
    return Outfit(
        id=f"fit_{uuid.uuid4().hex[:8]}",
        items=cart,
        owned=[],
        total=_total(cart),
        reason="The same look with cheaper pieces where it counts.",
        swaps={},
    )


async def _check(user_id: str, req: CartRequest) -> tuple[dict | None, list[CatalogItem], CartAllowed | CartRefused]:
    """Our own check, before Face ID. It never calls Stripe, so it answers fast."""
    known = catalog.items()
    items = [known[i] for i in req.item_ids if i in known]
    total = _total(items)
    row = await supabase.get_mandate(user_id, req.mandate_id)

    if not row or datetime.fromisoformat(row["expires_at"]) <= _now():
        if row and row.get("card_id") and stripe_issuing.configured():
            # The 24-hour expiry is ours to enforce, so retire the card too.
            await asyncio.to_thread(_cancel_quietly, row["card_id"])
        return row, items, CartRefused(
            status="refused",
            total=total,
            remaining=0,
            reason="expired",
            message="This spending limit has ended. Set a new one to keep shopping.",
        )

    remaining = round(float(row["limit"]) - float(row["spent"]), 2)
    unknown = [i for i in req.item_ids if i not in known]
    if unknown or not items:
        return row, items, CartRefused(
            status="refused",
            total=total,
            remaining=remaining,
            reason="not_apparel",
            message="This limit only covers clothing from our catalog, so the cart was refused.",
        )
    if total > remaining:
        return row, items, CartRefused(
            status="refused",
            total=total,
            remaining=remaining,
            reason="over_limit",
            message=(
                f"This cart is ${total - remaining:,.0f} over your ${float(row['limit']):,.0f} limit."
                if float(row["spent"]) == 0
                else f"This cart is ${total - remaining:,.0f} more than the ${remaining:,.0f} left on your limit."
            ),
            suggestion=_closest_under(items, remaining),
        )
    return row, items, CartAllowed(status="allowed", total=total, remaining=round(remaining - total, 2))


def _cancel_quietly(card_id: str) -> None:
    try:
        stripe_issuing.cancel_card(card_id)
    except Exception:
        log.exception("Couldn't cancel Stripe card %s", card_id)


@router.post("/checkout/mandate")
async def create_mandate(req: MandateRequest, user_id: str = Depends(supabase.current_user)) -> Mandate:
    if req.limit <= 0 or not 1 <= req.hours <= 24 * 7:
        raise HTTPException(422, "Set a limit above $0 that lasts between 1 hour and a week")
    card_id, label = None, FALLBACK_LABEL
    if stripe_issuing.configured():
        try:
            card = await asyncio.to_thread(stripe_issuing.create_agent_card, _cents(req.limit))
            card_id, label = card.id, stripe_issuing.card_label(card)
        except Exception:
            # Keep the demo working: the limit is still enforced in our code.
            log.exception("Stripe Issuing card creation failed; using the simulated card")
    row = await supabase.create_mandate(
        user_id,
        {
            "id": f"mandate_{uuid.uuid4().hex[:12]}",
            "limit": round(req.limit, 2),
            "spent": 0,
            "expires_at": (_now() + timedelta(hours=req.hours)).isoformat(),
            "card_id": card_id,
            "card_label": label,
        },
    )
    return _mandate(row)


@router.post("/checkout/cart")
async def check_cart(req: CartRequest, user_id: str = Depends(supabase.current_user)) -> CartAllowed | CartRefused:
    return (await _check(user_id, req))[2]


@router.post("/checkout/confirm")
async def confirm(req: CartRequest, user_id: str = Depends(supabase.current_user)) -> Receipt:
    # After Face ID. The same check runs again, in case anything changed since.
    row, items, verdict = await _check(user_id, req)
    if verdict.status == "refused" or not row:
        raise HTTPException(409, verdict.message if verdict.status == "refused" else "No spending limit found")

    authorization_id = None
    card_id = row.get("card_id")
    if card_id and stripe_issuing.configured():
        auth = await asyncio.to_thread(stripe_issuing.authorize, card_id, _cents(verdict.total))
        if not auth.approved:
            # The card's own limit caught something our check missed.
            raise HTTPException(409, f"The card declined the payment ({auth.decline_reason or 'declined'}).")
        authorization_id = auth.id

    spent = round(float(row["spent"]) + verdict.total, 2)
    # The card stays usable for what's left of the limit, and is cancelled when the mandate expires.
    await supabase.set_mandate_spent(user_id, row["id"], spent)

    return Receipt(
        order_id=f"order_{uuid.uuid4().hex[:12]}",
        items=items,
        total=verdict.total,
        remaining=round(float(row["limit"]) - spent, 2),
        card=CardRef(label=row["card_label"]),
        authorization_id=authorization_id,
        created_at=_now().isoformat(),
    )
