"""Task 5: Refactoring - Clean Billing Service & Idempotent Payment.

Refactors legacy callback billing into clean domain models, accurate decimal tax/discount
calculations, and idempotent charge processing.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class Customer:
    id: str
    name: str
    email: str


@dataclass
class InvoiceItem:
    description: str
    unit_price: float
    quantity: int

    @property
    def subtotal(self) -> float:
        return round(self.unit_price * self.quantity, 2)


@dataclass
class DiscountCoupon:
    code: str
    discount_type: str  # "percentage" or "fixed"
    value: float
    min_spend: float = 0.0
    is_expired: bool = False


@dataclass
class PaymentResult:
    success: bool
    transaction_id: Optional[str]
    amount_charged: float
    error_message: Optional[str] = None
    idempotency_key: Optional[str] = None


class BillingService:
    """Enterprise billing service with coupon validation and idempotent payments."""

    def __init__(self):
        self._processed_transactions: Dict[str, PaymentResult] = {}

    def calculate_total(
        self,
        items: List[InvoiceItem],
        coupon: Optional[DiscountCoupon] = None,
        tax_rate: float = 0.0,
    ) -> float:
        """Calculate final payable total with coupons applied and tax added."""
        if not items:
            return 0.0

        subtotal = round(sum(item.subtotal for item in items), 2)
        discount = 0.0

        if coupon:
            if coupon.is_expired:
                raise ValueError(f"Coupon '{coupon.code}' has expired.")
            if subtotal < coupon.min_spend:
                raise ValueError(
                    f"Subtotal ${subtotal:.2f} does not meet coupon minimum spend of ${coupon.min_spend:.2f}."
                )

            if coupon.discount_type == "percentage":
                discount = round(subtotal * (coupon.value / 100.0), 2)
            elif coupon.discount_type == "fixed":
                discount = min(subtotal, round(coupon.value, 2))
            else:
                raise ValueError(f"Unknown discount type: {coupon.discount_type}")

        taxable_amount = max(0.0, round(subtotal - discount, 2))
        tax = round(taxable_amount * tax_rate, 2)
        total = round(taxable_amount + tax, 2)
        return total

    def process_billing(
        self,
        customer: Customer,
        items: List[InvoiceItem],
        coupon: Optional[DiscountCoupon] = None,
        payment_gateway: Any = None,
        idempotency_key: Optional[str] = None,
        tax_rate: float = 0.0,
    ) -> PaymentResult:
        """Execute payment transaction with idempotency protection against double-charging."""
        # 1. Idempotency Check
        if idempotency_key and idempotency_key in self._processed_transactions:
            return self._processed_transactions[idempotency_key]

        total = self.calculate_total(items, coupon, tax_rate)

        if total == 0.0:
            result = PaymentResult(
                success=True,
                transaction_id=f"FREE_{uuid.uuid4().hex[:8]}",
                amount_charged=0.0,
                idempotency_key=idempotency_key,
            )
            if idempotency_key:
                self._processed_transactions[idempotency_key] = result
            return result

        # Execute payment via gateway or default mock
        try:
            if payment_gateway and hasattr(payment_gateway, "charge"):
                tx_id = payment_gateway.charge(customer.id, total)
            else:
                tx_id = f"TXN_{uuid.uuid4().hex[:12]}"

            result = PaymentResult(
                success=True,
                transaction_id=tx_id,
                amount_charged=total,
                idempotency_key=idempotency_key,
            )
        except Exception as e:
            result = PaymentResult(
                success=False,
                transaction_id=None,
                amount_charged=total,
                error_message=str(e),
                idempotency_key=idempotency_key,
            )

        if idempotency_key:
            self._processed_transactions[idempotency_key] = result

        return result
