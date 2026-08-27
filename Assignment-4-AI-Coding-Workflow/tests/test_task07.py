"""Self-contained test suite for Task 07: Unit & Property Test Suite for Order FSM."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

# Ensure assignment root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tasks.task_07_test_writing_order_fsm import (
    IllegalTransitionError,
    OrderStateMachine,
)


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
        with self.assertRaises(IllegalTransitionError):
            fsm.transition("CONFIRM_DELIVERY")
        self.assertEqual(fsm.current_state, OrderStateMachine.CREATED)

    def test_terminal_state_lock(self):
        """Verify terminal state CANCELLED cannot transition."""
        fsm = OrderStateMachine("ORD-103")
        fsm.transition("CANCEL")
        self.assertEqual(fsm.current_state, OrderStateMachine.CANCELLED)

        with self.assertRaises(IllegalTransitionError):
            fsm.transition("INITIATE_PAYMENT")
        self.assertEqual(fsm.current_state, OrderStateMachine.CANCELLED)


if __name__ == "__main__":
    unittest.main()
