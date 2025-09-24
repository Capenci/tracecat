
from fastapi import APIRouter
from pydantic import UUID4

from tracecat.cases.alerts.models import CaseAlertRead
from tracecat.cases.alerts.service import CaseAlertsService
from tracecat.cases.router import WorkspaceUser
from tracecat.db.dependencies import AsyncDBSession

router = APIRouter(prefix="/cases", tags=["cases"])

@router.get("/{case_id}/alerts", response_model=list[CaseAlertRead])
async def list_alerts(
    role: WorkspaceUser,
    session: AsyncDBSession,
    case_id: UUID4,
) -> list[CaseAlertRead]:
    """List all alerts for a case."""
    service = CaseAlertsService(session, role=role)
    alerts = await service.list_alerts_for_case(case_id)
    return [
        CaseAlertRead(
            id=alert.id,
            title=alert.title,
            description=alert.description,
            severity=alert.severity,
            status=alert.status,
            created_at=alert.created_at.isoformat(),
            updated_at=alert.updated_at.isoformat() if alert.updated_at else None,
        )
        for alert in alerts
    ]
@router.post("/{case_id}/alerts", response_model=CaseAlertRead)
async def add_alert(
    role: WorkspaceUser,
    session: AsyncDBSession,
    case_id: UUID4,
    alert_id: UUID4,
) -> CaseAlertRead:
    """Add an alert to a case."""
    service = CaseAlertsService(session, role=role)
    alert = await service.add_case_alert(case_id, alert_id)
    return CaseAlertRead(
        id=alert.id,
        title=alert.title,
        description=alert.description,
        severity=alert.severity,
        status=alert.status,
        created_at=alert.created_at.isoformat(),
        updated_at=alert.updated_at.isoformat() if alert.updated_at else None,
    )  
@router.delete("/{case_id}/alerts/{alert_id}", status_code=204)
async def remove_alert(
    role: WorkspaceUser,
    session: AsyncDBSession,
    case_id: UUID4,
    alert_id: UUID4,
) -> None:
    """Remove an alert from a case."""
    service = CaseAlertsService(session, role=role)
    await service.remove_case_alert(case_id, alert_id)