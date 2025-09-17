import uuid
from typing import Annotated, Literal
from fastapi import APIRouter, HTTPException, Query
from sqlalchemy.exc import DBAPIError, NoResultFound
from starlette.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_204_NO_CONTENT,
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
    HTTP_500_INTERNAL_SERVER_ERROR,
)

from tracecat.alerts.models import (
    AlertCommentCreate,
    AlertCommentRead,
    AlertCommentUpdate,
    AlertCreate,
    AlertCustomFieldRead,
    AlertFieldCreate,
    AlertFieldRead,
    AlertFieldUpdate,
    AlertRead,
    AlertReadMinimal,
    AlertUpdate
)
from tracecat.alerts.service import AlertCommentsService, AlertFieldsService, AlertsService
from tracecat.auth.credentials import RoleACL
from tracecat.auth.models import UserRead
from tracecat.auth.users import search_users
from tracecat.authz.models import WorkspaceRole
from tracecat.alerts.enums import AlertStatus, AlertSeverity, AlertPriority

from tracecat.db.dependencies import AsyncDBSession
from tracecat.logger import logger
from tracecat.tags.models import TagRead
from tracecat.tags.service import TagsService
from tracecat.types.auth import Role
from tracecat.types.pagination import (
    CursorPaginatedResponse,
    CursorPaginationParams,
)

alerts_router = APIRouter(prefix="/alerts", tags=["alerts"])
alert_fields_router = APIRouter(prefix="/alert-fields", tags=["alerts"])

WorkspaceUser = Annotated[
    Role,
    RoleACL(
        allow_user=True,
        allow_service=False,
        require_workspace="yes",
    ),
]

WorkspaceAdminUser = Annotated[
    Role,
    RoleACL(
        allow_user=True,
        allow_service=False,
        require_workspace="yes",
        require_workspace_roles=WorkspaceRole.ADMIN,
    ),
]

# Alert Management
@alerts_router.get("")
async def list_alerts(
    *,
    role: WorkspaceUser,
    session: AsyncDBSession,
    limit: int = Query(20, ge=1, le=100, description="Maximum items per page"),
    cursor: str | None = Query(None, description="Cursor for pagination"),
    reverse: bool = Query(False, description="Reverse the order of results"),
    search_term: str | None = Query(None, description="Search term to filter alerts"),
    status: AlertStatus | None = Query(None, description="Filter by alert status"),
    priority: AlertPriority | None = Query(None, description="Filter by alert priority"),
    severity: AlertSeverity | None = Query(None, description="Filter by alert severity"),
    tags: list[str] | None = Query(None, description="Filter by tag IDs or slugs (AND logic)"),
) -> CursorPaginatedResponse[AlertReadMinimal]:
    
    service = AlertsService(session,role)

    tag_ids = []
    if tags:
        tags_service = TagsService(session, role)
        for tag_identifier in tags:
            try:
                tag = await tags_service.get_tag_by_ref_or_id(tag_identifier)
                tag_ids.append(tag.id)
            except NoResultFound:
                continue
    
    pagination_params = CursorPaginationParams(
        limit=limit,
        cursor=cursor,
        reverse=reverse,
    )

    try:
        alerts = await service.list_alerts_paginated(
            pagination_params,
            search_term=search_term,
            status=status,
            priority=priority,
            severity=severity,
            tag_ids=tag_ids if tag_ids else None,
        )
    except Exception as e:
        logger.error(f"Failed to list alerts: {e}")
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve alerts",
        ) from e
    return alerts

@alerts_router.get("/search")
async def search_alerts(
    *,
    role: WorkspaceUser,
    session: AsyncDBSession,
    search_term: str | None = Query(
        None, description="Text to search for in alert summary and description"
    ),
    status: AlertStatus | None = Query(None, description="Filter by alert status"),
    priority: AlertPriority | None = Query(None, description="Filter by alert priority"),
    severity: AlertSeverity | None = Query(None, description="Filter by alert severity"),
    tags: list[str] | None = Query(
        None, description="Filter by tag IDs or slugs (AND logic)"
    ),
    limit: int | None = Query(None, description="Maximum number of alerts to return"),
    order_by: Literal["created_at", "updated_at", "priority", "severity", "status"]
    | None = Query(None, description="Field to order the cases by"),
    sort: Literal["asc", "desc"] | None = Query(
        None, description="Direction to sort (asc or desc)"
    ),
) -> list[AlertReadMinimal]:
    """Search cases based on various criteria."""
    service = AlertsService(session, role)

    # Convert tag identifiers to IDs
    tag_ids = []
    if tags:
        tags_service = TagsService(session, role)
        for tag_identifier in tags:
            try:
                tag = await tags_service.get_tag_by_ref_or_id(tag_identifier)
                tag_ids.append(tag.id)
            except NoResultFound:
                # Skip tags that do not exist in the workspace
                continue

    alerts = await service.search_alerts(
        search_term=search_term,
        status=status,
        priority=priority,
        severity=severity,
        tag_ids=tag_ids,
        limit=limit,
        order_by=order_by,
        sort=sort,
    )

    # Build case responses with tags (tags are already loaded via selectinload)
    alert_responses = []
    for alert in alerts:
        tag_reads = [
            TagRead.model_validate(tag, from_attributes=True) for tag in alert.tags
        ]

        alert_responses.append(
            AlertReadMinimal(
                id=alert.id,
                created_at=alert.created_at,
                updated_at=alert.updated_at,
                short_id=f"ALERT-{alert.alert_number:04d}",
                summary=alert.summary,
                status=alert.status,
                priority=alert.priority,
                severity=alert.severity,
                tags=tag_reads,
            )
        )

    return alert_responses


@alerts_router.get("/{alert_id}")
async def get_alert(
    *,
    role: WorkspaceUser,
    session: AsyncDBSession,
    alert_id: uuid.UUID,
) -> AlertRead:
    """Get a specific case."""
    service = AlertsService(session, role)
    alert = await service.get_alert(alert_id)
    if alert is None:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"Case with ID {alert_id} not found",
        )
    fields = await service.fields.get_fields(alert) or {}
    field_definitions = await service.fields.list_fields()
    final_fields = []
    for defn in field_definitions:
        f = AlertFieldRead.from_sa(defn)
        final_fields.append(
            AlertCustomFieldRead(
                id=f.id,
                type=f.type,
                description=f.description,
                nullable=f.nullable,
                default=f.default,
                reserved=f.reserved,
                value=fields.get(f.id),
            )
        )

    # Tags are already loaded via selectinload
    tag_reads = [TagRead.model_validate(tag, from_attributes=True) for tag in case.tags]

    # Match up the fields with the case field definitions
    return AlertRead(
        id=alert.id,
        short_id=f"CASE-{alert.case_number:04d}",
        created_at=alert.created_at,
        updated_at=alert.updated_at,
        summary=alert.summary,
        status=alert.status,
        priority=alert.priority,
        severity=alert.severity,
        description=alert.description,
        fields=final_fields,
        payload=alert.payload,
        tags=tag_reads,
    )

@alerts_router.post("", status_code=HTTP_201_CREATED)
async def create_alert(
    *,
    role: WorkspaceUser,
    session: AsyncDBSession,
    params: AlertCreate,
) -> None:
    """Create a new case."""
    service = AlertsService(session, role)
    await service.create_alert(params)


@alerts_router.patch("/{alert_id}", status_code=HTTP_204_NO_CONTENT)
async def update_alert(
    *,
    role: WorkspaceUser,
    session: AsyncDBSession,
    params: AlertUpdate,
    alert_id: uuid.UUID,
) -> None:
    """Update a case."""
    service = AlertsService(session, role)
    case = await service.get_alert(alert_id)
    if case is None:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"Case with ID {alert_id} not found",
        )
    try:
        await service.update_alert(case, params)
    except DBAPIError as e:
        while (cause := e.__cause__) is not None:
            e = cause
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e


@alerts_router.delete("/{alert_id}", status_code=HTTP_204_NO_CONTENT)
async def delete_case(
    *,
    role: WorkspaceAdminUser,
    session: AsyncDBSession,
    alert_id: uuid.UUID,
) -> None:
    """Delete a case."""
    service = AlertsService(session, role)
    alert = await service.get_case(alert_id)
    if alert is None:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"Case with ID {alert_id} not found",
        )
    await service.delete_case(alert)


# Case Comments
# Support comments as a first class activity type.
# We anticipate having other complex comment functionality in the future.
@alerts_router.get("/{alert_id}/comments", status_code=HTTP_200_OK)
async def list_comments(
    *,
    role: WorkspaceUser,
    session: AsyncDBSession,
    alert_id: uuid.UUID,
) -> list[AlertCommentRead]:
    """List all comments for a case."""
    # Get the case first
    service = AlertsService(session, role)
    case = await service.get_case(alert_id)
    if case is None:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"Case with ID {alert_id} not found",
        )
    # Execute join query directly in the endpoint
    comments_svc = AlertCommentsService(session, role)
    res = []
    for comment, user in await comments_svc.list_comments(case):
        comment_data = AlertCommentRead.model_validate(comment, from_attributes=True)
        if user:
            comment_data.user = UserRead.model_validate(user, from_attributes=True)
        res.append(comment_data)
    return res


@alerts_router.post("/{alert_id}/comments", status_code=HTTP_201_CREATED)
async def create_comment(
    *,
    role: WorkspaceUser,
    session: AsyncDBSession,
    alert_id: uuid.UUID,
    params: AlertCommentCreate,
) -> None:
    """Create a new comment on a alert."""
    alerts_svc = AlertsService(session, role)
    alert = await alerts_svc.get_alert(alert_id)
    if alert is None:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"Case with ID {alert_id} not found",
        )
    comments_svc = AlertCommentsService(session, role)
    await comments_svc.create_comment(alert, params)


@alerts_router.patch(
    "/{alert_id}/comments/{comment_id}",
    status_code=HTTP_204_NO_CONTENT,
)
async def update_comment(
    *,
    role: WorkspaceUser,
    session: AsyncDBSession,
    alert_id: uuid.UUID,
    comment_id: uuid.UUID,
    params: AlertCommentUpdate,
) -> None:
    """Update an existing comment."""
    alerts_svc = AlertsService(session, role)
    alert = await alerts_svc.get_alert(alert_id)
    if alert is None:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"alert with ID {alert_id} not found",
        )
    comments_svc = AlertCommentsService(session, role)
    comment = await comments_svc.get_comment(comment_id)
    if comment is None:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"Comment with ID {comment_id} not found",
        )
    await comments_svc.update_comment(comment, params)


@alerts_router.delete(
    "/{alert_id}/comments/{comment_id}", status_code=HTTP_204_NO_CONTENT
)
async def delete_comment(
    *,
    role: WorkspaceUser,
    session: AsyncDBSession,
    alert_id: uuid.UUID,
    comment_id: uuid.UUID,
) -> None:
    """Delete a comment."""
    alerts_svc = AlertsService(session, role)
    alert = await alerts_svc.get_alert(alert_id)
    if alert is None:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"Alert with ID {alert_id} not found",
        )
    comments_svc = AlertCommentsService(session, role)
    comment = await comments_svc.get_comment(comment_id)
    if comment is None:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"Comment with ID {comment_id} not found",
        )
    await comments_svc.delete_comment(comment)


# Case Fields


@alert_fields_router.get("")
async def list_fields(
    *,
    role: WorkspaceUser,
    session: AsyncDBSession,
) -> list[AlertFieldRead]:
    """List all case fields."""
    service = AlertFieldsService(session, role)
    columns = await service.list_fields()
    return [AlertFieldRead.from_sa(column) for column in columns]


@alert_fields_router.post("", status_code=HTTP_201_CREATED)
async def create_field(
    *,
    role: WorkspaceAdminUser,
    session: AsyncDBSession,
    params: AlertFieldCreate,
) -> None:
    """Create a new case field."""
    service = AlertFieldsService(session, role)
    await service.create_field(params)


@alert_fields_router.patch("/{field_id}", status_code=HTTP_204_NO_CONTENT)
async def update_field(
    *,
    role: WorkspaceAdminUser,
    session: AsyncDBSession,
    field_id: str,
    params: AlertFieldUpdate,
) -> None:
    """Update a case field."""
    service = AlertFieldsService(session, role)
    await service.update_field(field_id, params)


@alert_fields_router.delete("/{field_id}", status_code=HTTP_204_NO_CONTENT)
async def delete_field(
    *,
    role: WorkspaceAdminUser,
    session: AsyncDBSession,
    field_id: str,
) -> None:
    """Delete a case field."""
    service = AlertFieldsService(session, role)
    await service.delete_field(field_id)