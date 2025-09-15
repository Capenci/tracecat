from enum import StrEnum

class AlertPriority(StrEnum):
    """Alert priority values aligned with OCSF priority values.

    Values:
        UNKNOWN (0): The priority is unknown
        LOW (1): The priority is low
        MEDIUM (2): The priority is medium
        HIGH (3): The priority is high
        CRITICAL (4): The priority is critical
        OTHER (99): The priority is not normalized
    """

    UNKNOWN = "unknown"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    OTHER = "other"

class AlertSeverity(StrEnum):
    """Alert severity values aligned with OCSF severity values.

    Values:
        UNKNOWN (0): The event/finding severity is unknown
        INFORMATIONAL (1): Informational message. No action required
        LOW (2): The user decides if action is needed
        MEDIUM (3): Action is required but the situation is not serious at this time
        HIGH (4): Action is required immediately
        CRITICAL (5): Action is required immediately and the scope is broad
        FATAL (6): An error occurred but it is too late to take remedial action
        OTHER (99): The event/finding severity is not mapped
    """

    UNKNOWN = "unknown"
    INFORMATIONAL = "informational"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    FATAL = "fatal"
    OTHER = "other"

class AlertStatus(StrEnum):
    """Alert status values aligned with OCSF Incident Finding status."""

    UNKNOWN = "unknown"
    NEW = "new"
    IN_PROGRESS = "in_progress"
    ON_HOLD = "on_hold"
    RESOLVED = "resolved"
    CLOSED = "closed"
    OTHER = "other"