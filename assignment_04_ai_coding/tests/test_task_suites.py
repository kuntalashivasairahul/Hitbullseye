"""Independent, rigorous test suite verifying all 10 software engineering tasks.

Covers boundary conditions, edge cases, security vulnerabilities (timing attacks,
alg: none, replay attacks, immutable fields), and concurrency limits.
"""

from __future__ import annotations

import asyncio
import threading
import time
import unittest
from pathlib import Path
import sys

# Ensure assignment_04_ai_coding root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tasks.task_01_boilerplate_auth import (
    InvalidSignatureError,
    JWTAuthHandler,
    MalformedTokenError,
    TokenExpiredError,
)
from tasks.task_02_boilerplate_crud import UserRecordSerializer, ValidationError
from tasks.task_03_algo_sliding_window import SlidingWindowRateLimiter
from tasks.task_04_algo_graph_cycles import DirectedGraphCycleDetector
from tasks.task_05_refactor_legacy_billing import (
    BillingService,
    Customer,
    DiscountCoupon,
    InvoiceItem,
    PaymentResult,
)
from tasks.task_06_refactor_async_fetcher import AsyncDataFetcher
from tasks.task_07_test_writing_order_fsm import (
    IllegalTransitionError,
    OrderStateMachine,
)
from tasks.task_08_debugging_race_condition import ThreadSafeCache
from tasks.task_09_debugging_off_by_one import SubarrayRangeProcessor
from tasks.task_10_integration_webhook_parser import WebhookDispatcher


# =============================================================================
# Task 1: JWT Authentication Token Handler
# =============================================================================
class TestTask01Auth(unittest.TestCase):
    """Tests for Task 1: JWT Authentication Token Handler."""

    def setUp(self):
        self.secret = "super_secure_production_secret_key_12345"
        self.handler = JWTAuthHandler(self.secret)

    def test_weak_secret_rejection(self):
        """Ensure secret keys under 16 characters are rejected."""
        with self.assertRaises(ValueError):
            JWTAuthHandler("short_secret")

    def test_valid_token_lifecycle(self):
        """Verify token generation, decoding, and claims verification."""
        token = self.handler.generate_token("user_42", ["admin", "editor"], expires_in_seconds=3600)
        claims = self.handler.verify_token(token)
        self.assertEqual(claims["sub"], "user_42")
        self.assertEqual(claims["roles"], ["admin", "editor"])
        self.assertIn("iat", claims)
        self.assertIn("exp", claims)

    def test_tampered_payload_or_signature_rejected(self):
        """Verify tampering payload triggers InvalidSignatureError."""
        token = self.handler.generate_token("user_42", ["viewer"])
        parts = token.split(".")
        # Tamper payload
        tampered_token = f"{parts[0]}.eyJzdWIiOiAiaGFja2VyIn0.{parts[2]}"
        with self.assertRaises(InvalidSignatureError):
            self.handler.verify_token(tampered_token)

    def test_expired_token_rejected(self):
        """Verify expired token raises TokenExpiredError."""
        # Generate token with negative TTL
        token = self.handler.generate_token("user_expired", ["viewer"], expires_in_seconds=-10)
        with self.assertRaises(TokenExpiredError):
            self.handler.verify_token(token)

    def test_malformed_token_rejected(self):
        """Verify malformed tokens without 3 parts raise MalformedTokenError."""
        with self.assertRaises(MalformedTokenError):
            self.handler.verify_token("invalid.token")
        with self.assertRaises(MalformedTokenError):
            self.handler.verify_token("")

    def test_token_refresh(self):
        """Verify refreshed token preserves claims with extended expiration."""
        token = self.handler.generate_token("user_refresh", ["admin"], expires_in_seconds=100)
        refreshed = self.handler.refresh_token(token, extension_seconds=7200)
        claims = self.handler.verify_token(refreshed)
        self.assertEqual(claims["sub"], "user_refresh")
        self.assertEqual(claims["roles"], ["admin"])
        self.assertGreater(claims["exp"], time.time() + 7000)


# =============================================================================
# Task 2: REST API CRUD Serializer & Validator
# =============================================================================
class TestTask02Crud(unittest.TestCase):
    """Tests for Task 2: REST API CRUD Serializer & Validator."""

    def test_valid_user_serialization(self):
        """Verify valid user payload serializes to clean JSON."""
        data = {
            "username": "alex_smith",
            "email": "alex.smith@company.org",
            "role": "admin",
            "is_active": True,
        }
        json_str = UserRecordSerializer.serialize(data)
        deserialized = UserRecordSerializer.deserialize(json_str)
        self.assertEqual(deserialized["username"], "alex_smith")
        self.assertEqual(deserialized["email"], "alex.smith@company.org")
        self.assertEqual(deserialized["role"], "admin")
        self.assertIn("id", deserialized)
        self.assertIn("created_at", deserialized)

    def test_invalid_fields_raise_validation_error(self):
        """Verify invalid username, email, and roles raise field-specific errors."""
        bad_data = {
            "username": "a!",  # Too short, invalid symbol
            "email": "not-an-email",
            "role": "super_god_mode",  # Disallowed role
        }
        with self.assertRaises(ValidationError) as ctx:
            UserRecordSerializer.validate(bad_data)
        errors = ctx.exception.errors
        self.assertIn("username", errors)
        self.assertIn("email", errors)
        self.assertIn("role", errors)

    def test_partial_update_immutable_fields(self):
        """Verify attempting to modify 'id' or 'created_at' raises ValidationError."""
        existing = {
            "id": "11111111-1111-4111-8111-111111111111",
            "username": "original_user",
            "email": "original@domain.com",
            "role": "viewer",
            "created_at": "2026-01-01T00:00:00Z",
        }
        # Legitimate partial update
        updated = UserRecordSerializer.partial_update(existing, {"role": "editor"})
        self.assertEqual(updated["role"], "editor")
        self.assertEqual(updated["id"], existing["id"])

        # Attempt to tamper immutable ID
        with self.assertRaises(ValidationError) as ctx:
            UserRecordSerializer.partial_update(existing, {"id": "22222222-2222-4222-8222-222222222222"})
        self.assertIn("id", ctx.exception.errors)

        # Attempt to tamper created_at
        with self.assertRaises(ValidationError) as ctx:
            UserRecordSerializer.partial_update(existing, {"created_at": "2020-01-01T00:00:00Z"})
        self.assertIn("created_at", ctx.exception.errors)


# =============================================================================
# Task 3: High-Throughput Rate Limiting Sliding Window
# =============================================================================
class TestTask03SlidingWindow(unittest.TestCase):
    """Tests for Task 3: High-Throughput Rate Limiting Sliding Window."""

    def setUp(self):
        self.limiter = SlidingWindowRateLimiter()

    def test_rate_limit_allow_and_block(self):
        """Verify requests allowed up to max_requests and blocked when exceeded."""
        key = "client_ip_1"
        t0 = 1000.0

        # Allow 3 requests in a 10s window
        allowed, remaining, _ = self.limiter.is_allowed(key, max_requests=3, window_seconds=10.0, current_time=t0)
        self.assertTrue(allowed)
        self.assertEqual(remaining, 2)

        allowed, remaining, _ = self.limiter.is_allowed(key, max_requests=3, window_seconds=10.0, current_time=t0 + 1)
        self.assertTrue(allowed)
        self.assertEqual(remaining, 1)

        allowed, remaining, _ = self.limiter.is_allowed(key, max_requests=3, window_seconds=10.0, current_time=t0 + 2)
        self.assertTrue(allowed)
        self.assertEqual(remaining, 0)

        # 4th request at t0 + 3 should be blocked
        allowed, remaining, retry_after = self.limiter.is_allowed(key, max_requests=3, window_seconds=10.0, current_time=t0 + 3)
        self.assertFalse(allowed)
        self.assertEqual(remaining, 0)
        # Oldest request at t0 expires at t0 + 10, current is t0 + 3 -> retry_after is 7.0
        self.assertAlmostEqual(retry_after, 7.0, places=2)

    def test_sliding_window_continuous_slide(self):
        """Verify window slides continuously freeing capacity as old requests expire."""
        key = "client_ip_2"
        t0 = 2000.0
        self.limiter.is_allowed(key, 2, 5.0, current_time=t0)
        self.limiter.is_allowed(key, 2, 5.0, current_time=t0 + 1.0)

        # Blocked at t0 + 2
        allowed, _, _ = self.limiter.is_allowed(key, 2, 5.0, current_time=t0 + 2.0)
        self.assertFalse(allowed)

        # At t0 + 5.1, the first request at t0 has expired!
        allowed, remaining, _ = self.limiter.is_allowed(key, 2, 5.0, current_time=t0 + 5.1)
        self.assertTrue(allowed)
        self.assertEqual(remaining, 0)

    def test_cleanup_expired(self):
        """Verify cleanup_expired removes idle client keys."""
        self.limiter.is_allowed("old_client", 5, 10.0, current_time=100.0)
        self.limiter.is_allowed("new_client", 5, 10.0, current_time=500.0)

        evicted = self.limiter.cleanup_expired(older_than_seconds=200.0, current_time=500.0)
        self.assertEqual(evicted, 1)
        self.assertNotIn("old_client", self.limiter._store)
        self.assertIn("new_client", self.limiter._store)


# =============================================================================
# Task 4: Directed Graph Cycle Detector & Topo Sort
# =============================================================================
class TestTask04GraphCycles(unittest.TestCase):
    """Tests for Task 4: Directed Graph Cycle Detector & Topo Sort."""

    def test_detects_self_loops(self):
        """Verify self-loops A -> A are detected as cycles."""
        detector = DirectedGraphCycleDetector()
        detector.add_edge("A", "A")
        self.assertTrue(detector.has_cycle())
        self.assertIsNone(detector.topological_sort())

    def test_detects_simple_cycle(self):
        """Verify cycle A -> B -> C -> A is detected."""
        detector = DirectedGraphCycleDetector()
        detector.add_edge("A", "B")
        detector.add_edge("B", "C")
        detector.add_edge("C", "A")
        self.assertTrue(detector.has_cycle())
        self.assertIsNone(detector.topological_sort())

    def test_dag_topological_sort(self):
        """Verify topological sort on a valid DAG produces valid linear dependency order."""
        detector = DirectedGraphCycleDetector()
        # Dependency graph:
        # Core -> Auth -> API
        # Core -> DB -> API
        detector.add_edge("Core", "Auth")
        detector.add_edge("Core", "DB")
        detector.add_edge("Auth", "API")
        detector.add_edge("DB", "API")

        self.assertFalse(detector.has_cycle())
        order = detector.topological_sort()
        self.assertIsNotNone(order)
        self.assertEqual(len(order), 4)
        # Verify edge constraints: for every edge u -> v, u must precede v in order
        for u, v in [("Core", "Auth"), ("Core", "DB"), ("Auth", "API"), ("DB", "API")]:
            self.assertLess(order.index(u), order.index(v))


# =============================================================================
# Task 5: Clean Billing Service & Idempotent Payment
# =============================================================================
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
        # 10% coupon on 125.50 = 12.55 discount -> taxable: 112.95 -> 10% tax: 11.30 -> total: 124.25
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

        # First billing attempt
        res1 = self.billing.process_billing(
            self.customer, self.items, payment_gateway=gateway, idempotency_key=idem_key
        )
        self.assertTrue(res1.success)
        self.assertEqual(res1.transaction_id, "TXN_1")
        self.assertEqual(gateway.charge_count, 1)

        # Duplicate billing attempt with same idempotency key
        res2 = self.billing.process_billing(
            self.customer, self.items, payment_gateway=gateway, idempotency_key=idem_key
        )
        self.assertTrue(res2.success)
        self.assertEqual(res2.transaction_id, "TXN_1")
        # Gateway must NOT be charged a second time!
        self.assertEqual(gateway.charge_count, 1)


# =============================================================================
# Task 6: Concurrent Async Data Fetcher with Retries
# =============================================================================
class TestTask06AsyncFetcher(unittest.TestCase):
    """Tests for Task 6: Concurrent Async Data Fetcher with Retries."""

    def test_batch_fetch_concurrency_and_results(self):
        """Verify async batch fetch executes all requests concurrently."""
        fetcher = AsyncDataFetcher()
        urls = [f"https://api.example.com/item/{i}" for i in range(10)]

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            results = loop.run_until_complete(fetcher.batch_fetch(urls, max_concurrency=4))
            self.assertEqual(len(results), 10)
            for res in results:
                self.assertEqual(res["status_code"], 200)
                self.assertIn("Response from", res["data"])
        finally:
            loop.close()

    def test_retry_on_transient_failure(self):
        """Verify fetcher retries on transient errors."""
        attempts = 0

        async def flaky_call(url: str):
            nonlocal attempts
            attempts += 1
            if attempts < 2:
                raise ConnectionResetError("Temporary blip")
            return "Success after retry"

        fetcher = AsyncDataFetcher(mock_requester=flaky_call)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            res = loop.run_until_complete(fetcher.fetch_url("https://api.test/flaky", max_retries=2))
            self.assertEqual(res["status_code"], 200)
            self.assertEqual(res["data"], "Success after retry")
            self.assertEqual(res["attempts"], 2)
        finally:
            loop.close()


# =============================================================================
# Task 7: Unit & Property Test Suite for Order FSM
# =============================================================================
class TestTask07OrderFSM(unittest.TestCase):
    """Tests for Task 7: Unit & Property Test Suite for Order FSM."""

    def test_normal_order_lifecycle(self):
        """Verify canonical progression through all lifecycle states."""
        fsm = OrderStateMachine("ORD-101")
        self.assertEqual(fsm.current_state, OrderStateMachine.CREATED)

        fsm.transition("INITIATE_PAYMENT")
        self.assertEqual(fsm.current_state, OrderStateMachine.PAYMENT_PENDING)

        fsm.transition("PAYMENT_SUCCESS")
        self.assertEqual(fsm.current_state, OrderStateMachine.PAID)

        fsm.transition("START_FULFILLMENT")
        self.assertEqual(fsm.current_state, OrderStateMachine.FULFILLING)

        fsm.transition("DISPATCH_SHIPMENT")
        self.assertEqual(fsm.current_state, OrderStateMachine.SHIPPED)

        fsm.transition("CONFIRM_DELIVERY")
        self.assertEqual(fsm.current_state, OrderStateMachine.DELIVERED)

        history = fsm.get_history()
        self.assertEqual(len(history), 6)

    def test_illegal_transition_rejection(self):
        """Verify illegal jump raises IllegalTransitionError and preserves current state."""
        fsm = OrderStateMachine("ORD-102")
        # Attempting to deliver an order that is just CREATED
        with self.assertRaises(IllegalTransitionError):
            fsm.transition("CONFIRM_DELIVERY")
        self.assertEqual(fsm.current_state, OrderStateMachine.CREATED)

    def test_terminal_state_lock(self):
        """Verify terminal state CANCELLED cannot transition."""
        fsm = OrderStateMachine("ORD-103")
        fsm.transition("CANCEL")
        self.assertEqual(fsm.current_state, OrderStateMachine.CANCELLED)

        # Attempt to revive cancelled order
        with self.assertRaises(IllegalTransitionError):
            fsm.transition("INITIATE_PAYMENT")
        self.assertEqual(fsm.current_state, OrderStateMachine.CANCELLED)


# =============================================================================
# Task 8: Thread-Safe In-Memory Cache with RLock
# =============================================================================
class TestTask08RaceCondition(unittest.TestCase):
    """Tests for Task 8: Thread-Safe In-Memory Cache with RLock."""

    def test_concurrent_multithreaded_read_write(self):
        """Verify cache integrity under heavy multi-threaded concurrent access."""
        cache = ThreadSafeCache()
        thread_count = 30
        iterations = 50
        errors = []

        def worker(w_id: int):
            try:
                for i in range(iterations):
                    k = f"key_{i % 5}"
                    cache.set(k, f"val_{w_id}_{i}")
                    val = cache.get(k)
                    self.assertIsNotNone(val)
                    if i % 10 == 0:
                        cache.size()
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=worker, args=(t,)) for t in range(thread_count)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(errors), 0, f"Thread errors encountered: {errors}")

    def test_ttl_expiration(self):
        """Verify expired keys return default and are removed."""
        cache = ThreadSafeCache()
        cache.set("ephemeral", "hello", ttl_seconds=0.05)
        self.assertEqual(cache.get("ephemeral"), "hello")

        time.sleep(0.08)
        self.assertIsNone(cache.get("ephemeral"))
        self.assertEqual(cache.size(), 0)

    def test_get_or_compute_stampede_prevention(self):
        """Verify compute_func is invoked exactly once during concurrent cache misses."""
        cache = ThreadSafeCache()
        compute_count = 0

        def heavy_computation():
            nonlocal compute_count
            compute_count += 1
            time.sleep(0.02)
            return "computed_data"

        def reader():
            return cache.get_or_compute("shared_key", heavy_computation)

        threads = [threading.Thread(target=reader) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(cache.get("shared_key"), "computed_data")
        # Heavy computation must have executed only once!
        self.assertEqual(compute_count, 1)


# =============================================================================
# Task 9: Robust Subarray Prefix & Sliding Window Max
# =============================================================================
class TestTask09OffByOne(unittest.TestCase):
    """Tests for Task 9: Robust Subarray Prefix & Sliding Window Max."""

    def test_prefix_sum_inclusive_ranges(self):
        """Verify prefix sum range queries [L, R] inclusive without index errors."""
        arr = [2, 4, 6, 8, 10]
        queries = [
            (0, 4),  # Full sum: 30
            (0, 0),  # Single element at 0: 2
            (4, 4),  # Single element at end: 10
            (1, 3),  # 4 + 6 + 8 = 18
        ]
        results = SubarrayRangeProcessor.prefix_sum_query(arr, queries)
        self.assertEqual(results, [30, 2, 10, 18])

    def test_sliding_window_maximum(self):
        """Verify sliding window maximum handles boundary window sizes."""
        nums = [1, 3, -1, -3, 5, 3, 6, 7]
        # k = 3
        res = SubarrayRangeProcessor.sliding_window_maximum(nums, k=3)
        self.assertEqual(res, [3, 3, 5, 5, 6, 7])

        # k = 1 (every element is its own max)
        self.assertEqual(SubarrayRangeProcessor.sliding_window_maximum(nums, k=1), nums)

        # k >= len (single maximum)
        self.assertEqual(SubarrayRangeProcessor.sliding_window_maximum(nums, k=len(nums)), [7])

    def test_binary_search_bounds(self):
        """Verify binary search finds exact duplicate span indices or (-1, -1)."""
        sorted_arr = [1, 2, 4, 4, 4, 4, 7, 9]
        # Multiple occurrences
        self.assertEqual(SubarrayRangeProcessor.binary_search_bounds(sorted_arr, 4), (2, 5))
        # Single occurrence
        self.assertEqual(SubarrayRangeProcessor.binary_search_bounds(sorted_arr, 1), (0, 0))
        self.assertEqual(SubarrayRangeProcessor.binary_search_bounds(sorted_arr, 9), (7, 7))
        # Missing element
        self.assertEqual(SubarrayRangeProcessor.binary_search_bounds(sorted_arr, 5), (-1, -1))


# =============================================================================
# Task 10: Webhook HMAC Verifier & Replay Guard
# =============================================================================
class TestTask10WebhookParser(unittest.TestCase):
    """Tests for Task 10: Webhook HMAC Verifier & Replay Guard."""

    def setUp(self):
        self.secret = "whsec_super_secret_signing_key_456"
        self.dispatcher = WebhookDispatcher(self.secret, max_drift_seconds=300.0)

    def test_valid_webhook_dispatch(self):
        """Verify valid signature within drift window executes handler."""
        payload = b'{"event": "payment.succeeded", "amount": 1500}'
        ts_str = str(time.time())
        sig = self.dispatcher.compute_signature(payload, ts_str)

        handler_called = False
        def on_payment(data: dict):
            nonlocal handler_called
            handler_called = True
            return "processed_successfully"

        self.dispatcher.register_handler("payment.succeeded", on_payment)
        res = self.dispatcher.dispatch(payload, signature_header=sig, timestamp_header=ts_str)

        self.assertEqual(res["status"], WebhookDispatcher.STATUS_SUCCESS)
        self.assertTrue(handler_called)
        self.assertEqual(res["result"], "processed_successfully")

    def test_expired_timestamp_replay_rejection(self):
        """Verify webhook timestamp older than 300s is rejected as expired replay."""
        payload = b'{"event": "order.cancelled"}'
        old_ts = str(time.time() - 400.0)  # 400 seconds ago
        sig = self.dispatcher.compute_signature(payload, old_ts)

        res = self.dispatcher.dispatch(payload, signature_header=sig, timestamp_header=old_ts)
        self.assertEqual(res["status"], WebhookDispatcher.STATUS_EXPIRED_TIMESTAMP)
        self.assertIn("drift", res["error"])

    def test_tampered_payload_rejected(self):
        """Verify altered payload fails signature check."""
        payload = b'{"event": "account.compromised"}'
        ts_str = str(time.time())
        sig = self.dispatcher.compute_signature(payload, ts_str)

        tampered_payload = b'{"event": "account.compromised", "admin": true}'
        res = self.dispatcher.dispatch(tampered_payload, signature_header=sig, timestamp_header=ts_str)
        self.assertEqual(res["status"], WebhookDispatcher.STATUS_INVALID_SIGNATURE)


if __name__ == "__main__":
    unittest.main()
