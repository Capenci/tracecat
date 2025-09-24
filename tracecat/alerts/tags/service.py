import uuid
from collections.abc import Sequence

from sqlmodel import select

from tracecat.db.schemas import AlertTag, Tag
from tracecat.identifiers import TagID
from tracecat.service import BaseWorkspaceService
from tracecat.tags.service import TagsService


class AlertTagsService(BaseWorkspaceService):
    service_name = "alert_tags"

    async def list_tags_for_alert(self, alert_id: uuid.UUID) -> Sequence[Tag]:
        """List all tags for a case."""
        stmt = select(Tag).join(AlertTag).where(AlertTag.alert_id == alert_id)
        result = await self.session.exec(stmt)
        return result.all()

    async def get_alert_tag(self, alert_id: uuid.UUID, tag_id: TagID) -> AlertTag | None:
        """Get a case tag association."""
        stmt = select(AlertTag).where(
            AlertTag.alert_id == alert_id, AlertTag.tag_id == tag_id
        )
        result = await self.session.exec(stmt)
        return result.one_or_none()

    async def add_alert_tag(self, alert_id: uuid.UUID, tag_identifier: str) -> Tag:
        """Add a tag to a case by ID or ref."""
        # Resolve tag identifier to ID
        tags_service = TagsService(self.session, self.role)
        tag = await tags_service.get_tag_by_ref_or_id(tag_identifier)

        # Check if already exists
        stmt = select(AlertTag).where(
            AlertTag.alert_id == alert_id, AlertTag.tag_id == tag.id
        )
        result = await self.session.exec(stmt)
        existing = result.one_or_none()

        if existing:
            return tag  # Already exists, return tag

        # Create new
        alert_tag = AlertTag(alert_id=alert_id, tag_id=tag.id)
        self.session.add(alert_tag)

        await self.session.commit()
        await self.session.refresh(tag)
        return tag

    async def remove_alert_tag(self, alert_id: uuid.UUID, tag_identifier: str) -> None:
        """Remove a tag from a alert by ID or ref."""
        tags_service = TagsService(self.session, self.role)
        tag = await tags_service.get_tag_by_ref_or_id(tag_identifier)

        alert_tag = await self.get_alert_tag(alert_id, tag.id)
        if not alert_tag:
            raise ValueError(f"Tag {tag_identifier} not found on alert {alert_id}")
        await self.session.delete(alert_tag)
        await self.session.commit()
