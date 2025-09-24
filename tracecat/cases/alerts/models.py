from pydantic import BaseModel, Field

from tracecat.alerts import AlertID

class CaseAlertCreate(BaseModel):
    alert_id: AlertID = Field(
        description="Alert ID (UUID)",
    )

class CaseAlertRead(BaseModel):
    """Alert data."""

    id: AlertID
    title: str
    description: str | None
    severity: str
    status: str
    created_at: str
    updated_at: str | None