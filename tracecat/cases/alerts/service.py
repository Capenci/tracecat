import uuid
from collections.abc import Sequence

from sqlmodel import select

from tracecat.db.schemas import Alert, CaseAlert
from tracecat.service import BaseWorkspaceService

class CaseAlertsService(BaseWorkspaceService):
    service_name = "case_alerts"

    async def list_alerts_for_case(self, case_id: uuid.UUID) -> Sequence[Alert]:
        """List all alerts for a case."""
        stmt = select(Alert).join(CaseAlert).where(CaseAlert.case_id == case_id and Alert.id == CaseAlert.alert_id)
        result = await self.session.exec(stmt)
        return result.all()
    
    async def get_case_alert(self, case_id: uuid.UUID, alert_id: uuid.UUID) -> CaseAlert | None:
        """Get a case alert association."""
        stmt = select(CaseAlert).where(
            CaseAlert.case_id == case_id, CaseAlert.alert_id == alert_id
        )
        result = await self.session.exec(stmt)
        return result.one_or_none()

    async def add_case_alert(self, case_id: uuid.UUID, alert_id: uuid.UUID) -> Alert:
        """Add an alert to a case."""
        # Check if already exists
        stmt = select(CaseAlert).where(
            CaseAlert.case_id == case_id, CaseAlert.alert_id == alert_id
        )
        result = await self.session.exec(stmt)
        existing = result.one_or_none()

        if existing:
            # Already exists, return alert
            stmt = select(Alert).where(Alert.id == alert_id)
            result = await self.session.exec(stmt)
            alert = result.one()
            return alert

        # Create new
        case_alert = CaseAlert(case_id=case_id, alert_id=alert_id)
        self.session.add(case_alert)

        await self.session.commit()
        
        # Return the added alert
        stmt = select(Alert).where(Alert.id == alert_id)
        result = await self.session.exec(stmt)
        alert = result.one()
        
        return alert
    async def remove_case_alert(self, case_id: uuid.UUID, alert_id: uuid.UUID) -> None:
        """Remove an alert from a case."""
        case_alert = await self.get_case_alert(case_id, alert_id)
        if not case_alert:
            raise ValueError(f"Alert {alert_id} not found on case {case_id}")

        await self.session.delete(case_alert)
        await self.session.commit()



