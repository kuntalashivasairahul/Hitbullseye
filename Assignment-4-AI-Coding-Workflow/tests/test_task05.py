"""Self-contained test suite for Task 05: Clean Billing Service & Idempotent Payment."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

# Ensure assignment root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tasks.task_05_refactor_legacy_billing import (
    BillingService,
    Customer,
    DiscountCoupon,
    InvoiceItem,
    PaymentResult,
)


class TestTask05LegacyBilling(unittest.TestCase):
    """Tests for Task 5: Clean Billing Service & Idempotent Payment."""

    def setUp(self):
        self.billing = BillingService()
        self.customer = Customer("cust_1", "Jane Doe", "jane@example.com")
        self.items = [
            InvoiceItem("Widget A", 50.0, 2),  # 100.00
            InvoiceItem("Widget B", 25.5, 1),  #  25.50 -> Subtotal: 125.50
        ]

    def test_calculate_total_with_coupons_and_tax(self):
        """Verify total calculation with percentage coupon and tax."""
        coupon = DiscountCoupon("SAVE10", "percentage", 10.0, min_spend=50.0)
        total = self.billing.calculate_total(self.items, coupon=coupon, tax_rate=0.10)
        self.assertEqual(total, 124.25)

    def test_expired_coupon_rejected(self):
        """Verify expired coupon raises ValueError."""
        expired_coupon = DiscountCoupon("OLD50", "fixed", 10.0, is_expired=True)
        with self.assertRaises(ValueError):
            self.billing.calculate_total(self.items, coupon=expired_coupon)

    def test_idempotency_prevents_double_charging(self):
        """Verify identical idempotency_key returns cached result without charging again."""
        class MockGateway:
            charge_count = 0
            def charge(self, cust_id, amount):
                self.charge_count += 1
                return f"TXN_{self.charge_count}"

        gateway = MockGateway()
        idem_key = "order_uniq_9999"

        res1 = self.billing.process_billing(
            self.customer, self.items, payment_gateway=gateway, idempotency_key=idem_key
        )
        self.assertTrue(res1.success)
        self.assertEqual(res1.transaction_id, "TXN_1")
        self.assertEqual(gateway.charge_count, 1)

        res2 = self.billing.process_billing(
            self.customer, self.items, payment_gateway=gateway, idempotency_key=idem_key
        )
        self.assertTrue(res2.success)
        self.assertEqual(res2.transaction_id, "TXN_1")
        self.assertEqual(gateway.charge_count, 1)


if __name__ == "__main__":
    unittest.main()
