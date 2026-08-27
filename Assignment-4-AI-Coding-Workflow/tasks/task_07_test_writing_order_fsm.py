"""Task 7: Test Writing - Unit & Property Test Suite for Order FSM.

Implements an e-commerce finite state machine with strict transition invariants,
terminal state locking, and complete history audit logging.
"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional, Set


class IllegalTransitionError(Exception):
    """Raised when an invalid state transition is attempted."""
    pass


class OrderStateMachine:
    """Finite State Machine managing e-commerce order lifecycles."""

    CREATED = "CREATED"
    PAYMENT_PENDING = "PAYMENT_PENDING"
    PAID = "PAID"
    FULFILLING = "FULFILLING"
    SHIPPED = "SHIPPED"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"
    REFUNDED = "REFUNDED"

    # Permitted state transitions: current_state -> set of valid next states
    TRANSITIONS: Dict[str, Set[str]] = {
        CREATED: {PAYMENT_PENDING, CANCELLED},
        PAYMENT_PENDING: {PAID, CANCELLED},
        PAID: {FULFILLING, REFUNDED},
        FULFILLING: {SHIPPED, CANCELLED},
        SHIPPED: {DELIVERED},
        DELIVERED: {REFUNDED},
        CANCELLED: set(),   # Terminal state
        REFUNDED: set(),    # Terminal state
    }

    # Event names mapped to target states
    EVENT_MAP: Dict[str, str] = {
        "INITIATE_PAYMENT": PAYMENT_PENDING,
        "PAYMENT_SUCCESS": PAID,
        "START_FULFILLMENT": FULFILLING,
        "DISPATCH_SHIPMENT": SHIPPED,
        "CONFIRM_DELIVERY": DELIVERED,
        "CANCEL": CANCELLED,
        "REFUND": REFUNDED,
    }

    def __init__(self, order_id: str):
        self.order_id = order_id
        self.current_state = self.CREATED
        self._history: List[Dict[str, Any]] = [
            {
                "from_state": None,
                "to_state": self.CREATED,
                "event": "INITIALIZED",
                "timestamp": time.time(),
                "metadata": {},
            }
        ]

    def can_transition(self, event: str) -> bool:
        """Check if an event is permissible from the current state."""
        target_state = self.EVENT_MAP.get(event)
        if not target_state:
            return False
        valid_next_states = self.TRANSITIONS.get(self.current_state, set())
        return target_state in valid_next_states

    def transition(self, event: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Advance the FSM state or raise IllegalTransitionError."""
        target_state = self.EVENT_MAP.get(event)
        if not target_state:
            raise IllegalTransitionError(f"Unknown event '{event}'. Valid events: {sorted(self.EVENT_MAP.keys())}")

        valid_next_states = self.TRANSITIONS.get(self.current_state, set())
        if target_state not in valid_next_states:
            raise IllegalTransitionError(
                f"Cannot transition from '{self.current_state}' to '{target_state}' via event '{event}'."
            )

        prev_state = self.current_state
        self.current_state = target_state
        self._history.append({
            "from_state": prev_state,
            "to_state": target_state,
            "event": event,
            "timestamp": time.time(),
            "metadata": metadata or {},
        })

    def get_history(self) -> List[Dict[str, Any]]:
        """Return defensive copy of transition audit history."""
        return [dict(entry) for entry in self._history]
