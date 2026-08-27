"""Tasks package for Assignment 4: AI-Assisted Coding Workflow."""

from .task_01_boilerplate_auth import (
    AuthError,
    InvalidSignatureError,
    JWTAuthHandler,
    MalformedTokenError,
    TokenExpiredError,
)
from .task_02_boilerplate_crud import UserRecordSerializer, ValidationError
from .task_03_algo_sliding_window import SlidingWindowRateLimiter
from .task_04_algo_graph_cycles import DirectedGraphCycleDetector
from .task_05_refactor_legacy_billing import (
    BillingService,
    Customer,
    DiscountCoupon,
    InvoiceItem,
    PaymentResult,
)
from .task_06_refactor_async_fetcher import AsyncDataFetcher
from .task_07_test_writing_order_fsm import (
    IllegalTransitionError,
    OrderStateMachine,
)
from .task_08_debugging_race_condition import ThreadSafeCache
from .task_09_debugging_off_by_one import SubarrayRangeProcessor
from .task_10_integration_webhook_parser import WebhookDispatcher

__all__ = [
    "JWTAuthHandler",
    "AuthError",
    "TokenExpiredError",
    "InvalidSignatureError",
    "MalformedTokenError",
    "UserRecordSerializer",
    "ValidationError",
    "SlidingWindowRateLimiter",
    "DirectedGraphCycleDetector",
    "BillingService",
    "Customer",
    "InvoiceItem",
    "DiscountCoupon",
    "PaymentResult",
    "AsyncDataFetcher",
    "OrderStateMachine",
    "IllegalTransitionError",
    "ThreadSafeCache",
    "SubarrayRangeProcessor",
    "WebhookDispatcher",
]
