import logging
from enum import Enum
from PyQt6.QtCore import QObject, pyqtSignal

logger = logging.getLogger("SEEZY")

class SessionState(Enum):
    IDLE = "IDLE"
    ACTIVE = "ACTIVE"

class OperatingMode(Enum):
    MANUAL = "MANUAL"
    AUTO = "AUTO"

class SystemStatus(Enum):
    READY = "READY"
    RUNNING = "RUNNING"
    HALTED = "HALTED"
    ERROR = "ERROR"
    DISCONNECTED = "DISCONNECTED"

class StateManager(QObject):
    # Signal emitted whenever any state changes (session, mode, status)
    state_changed = pyqtSignal(SessionState, OperatingMode, SystemStatus)

    def __init__(self):
        super().__init__()
        self.session = SessionState.IDLE
        self.mode = OperatingMode.MANUAL
        self.status = SystemStatus.READY

    def set_session(self, state: SessionState):
        if self.session != state:
            self.session = state
            self._emit_change()

    def set_mode(self, mode: OperatingMode):
        if self.mode != mode:
            self.mode = mode
            self._emit_change()

    def set_status(self, status: SystemStatus):
        if self.status != status:
            self.status = status
            self._emit_change()

    def _emit_change(self):
        """Log the change and notify the UI."""
        logger.info(f"State Transition -> Session: {self.session.value} | Mode: {self.mode.value} | Status: {self.status.value}")
        self.state_changed.emit(self.session, self.mode, self.status)