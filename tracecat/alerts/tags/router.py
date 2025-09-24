from typing import Annotated

from fastapi import APIRouter, HTTPException, status
from pydantic import UUID4
from sqlalchemy.exc import IntegrityError, NoResultFound

from tracecat.alerts.tags.models import AlertTagCreate, AlertTagRead
from tracecat.alerts.tags.service import AlertTagsService
from tracecat.auth.credentials import RoleACL
from tracecat.db.dependencies import AsyncDBSession
from tracecat.types.auth import Role

WorkspaceUser = Annotated[
    Role,
    RoleACL(
        allow_user=True,
        allow_service=False,
        require_workspace="yes",
    ),
]

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("/{alert_id}/tags", response_model=list[AlertTagRead])
async def list_tags(
    role: WorkspaceUser,
    session: AsyncDBSession,
    alert_id: UUID4,
) -> list[AlertTagRead]:
    """List all tags for a case."""
    service = AlertTagsService(session, role=role)
    tags = await service.list_tags_for_alert(alert_id)
    return [
        AlertTagRead(id=tag.id, name=tag.name, ref=tag.ref, color=tag.color)
        for tag in tags
    ]


@router.post(
    "/{alert_id}/tags", status_code=status.HTTP_201_CREATED, response_model=AlertTagRead
)
async def add_tag(
    role: WorkspaceUser,
    session: AsyncDBSession,
    alert_id: UUID4,
    params: AlertTagCreate,
) -> AlertTagRead:
    """Add a tag to a case using tag ID or slug."""
    service = AlertTagsService(session, role=role)
    try:
        tag = await service.add_alert_tag(alert_id, str(params.tag_id))
        return AlertTagRead(id=tag.id, name=tag.name, ref=tag.ref, color=tag.color)
    except NoResultFound as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found"
        ) from err
    except IntegrityError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Tag operation failed"
        ) from e


@router.delete(
    "/{alert_id}/tags/{tag_identifier}", status_code=status.HTTP_204_NO_CONTENT
)
async def remove_tag(
    role: WorkspaceUser,
    session: AsyncDBSession,
    alert_id: UUID4,
    tag_identifier: str,  # Can be UUID or ref
) -> None:
    """Remove a tag from a case using tag ID or ref."""
    service = AlertTagsService(session, role=role)
    try:
        await service.remove_alert_tag(alert_id, tag_identifier)
    except NoResultFound as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found on case"
        ) from err
