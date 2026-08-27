"""Source package for Assignment 4: AI-Assisted Coding Workflow."""

from .task_manager import TaskManager
from .telemetry_runner import DefectEntry, TaskTelemetry, TelemetryRunner

__all__ = [
    "TaskManager",
    "TelemetryRunner",
    "TaskTelemetry",
    "DefectEntry",
]
__version__ = "0.2.0"
