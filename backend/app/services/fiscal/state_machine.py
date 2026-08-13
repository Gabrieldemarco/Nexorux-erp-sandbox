import structlog
from enum import Enum
from typing import Dict, Optional

logger = structlog.get_logger(__name__)


class FiscalState(str, Enum):
    DRAFT = "draft"
    PENDING_SIGN = "pending_sign"
    PENDING_SEND = "pending_send"
    SENT = "sent"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


TERMINAL_STATES: set = {FiscalState.ACCEPTED, FiscalState.REJECTED, FiscalState.CANCELLED}


FISCAL_TRANSITIONS: Dict[str, set] = {
    FiscalState.DRAFT: {FiscalState.PENDING_SIGN, FiscalState.CANCELLED},
    FiscalState.PENDING_SIGN: {FiscalState.PENDING_SEND, FiscalState.DRAFT, FiscalState.CANCELLED},
    FiscalState.PENDING_SEND: {FiscalState.SENT, FiscalState.DRAFT, FiscalState.CANCELLED},
    FiscalState.SENT: {FiscalState.ACCEPTED, FiscalState.REJECTED, FiscalState.PENDING_SEND},
    FiscalState.REJECTED: {FiscalState.PENDING_SEND, FiscalState.DRAFT, FiscalState.CANCELLED},
    FiscalState.ACCEPTED: set(),
    FiscalState.CANCELLED: set(),
}


class FiscalStateMachine:
    """State machine for fiscal document lifecycle."""

    @staticmethod
    def can_transition(current_state: str, target_state: str) -> bool:
        allowed = FISCAL_TRANSITIONS.get(current_state, set())
        return target_state in allowed

    @staticmethod
    def transition(current_state: str, target_state: str, reason: Optional[str] = None) -> str:
        logger.info(
            "fiscal_state_transition",
            current_state=current_state,
            target_state=target_state,
            reason=reason,
        )

        if not FiscalStateMachine.can_transition(current_state, target_state):
            raise StateTransitionError(
                f"Cannot transition from {current_state} to {target_state}"
            )

        return target_state

    @staticmethod
    def is_terminal(state: str) -> bool:
        return state in TERMINAL_STATES

    @staticmethod
    def is_recoverable(state: str) -> bool:
        return state not in TERMINAL_STATES


class StateTransitionError(Exception):
    """Raised when an invalid state transition is attempted."""

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message
