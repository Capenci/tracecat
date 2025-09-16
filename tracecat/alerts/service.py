import uuid
from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any, Literal

import sqlalchemy as sa
from asyncpg import UndefinedColumnError
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.orm import aliased, selectinload
from sqlmodel import and_, cast, col, desc, func, or_, select
from sqlmodel.ext.asyncio.session import AsyncSession

from tracecat.auth.models import UserRead
from tracecat.alerts.enums import AlertStatus, AlertSeverity, AlertPriority
from tracecat.alerts.models import (
    AlertCommentCreate,
    AlertCommentUpdate,
    AlertReadMinimal,
    AlertRead,
    AlertCreate,
    AlertUpdate,
    AlertFieldRead,
    AlertFieldCreate,
    AlertFieldUpdate,
    AlertCustomFieldRead,
    FieldDiff,
)
from tracecat.contexts import ctx_run
from tracecat.db.schemas import (
    Alert,
    AlertComment,
    AlertFields,
    AlertTag,
    User,
)
from tracecat.service import BaseWorkspaceService
from tracecat.tables.service import TableEditorService, TablesService
from tracecat.tags.models import TagRead
from tracecat.types.auth import Role
from tracecat.types.exceptions import (
    TracecatAuthorizationError,
    TracecatException,
)
from tracecat.types.pagination import (
    BaseCursorPaginator,
    CursorPaginatedResponse,
    CursorPaginationParams,
)


class AlertsService(BaseWorkspaceService):
    service_name = "alerts"

    def __init__(self, session: AsyncSession, role: Role | None = None):
        super().__init__(session, role)
        self.tables = TablesService(session=self.session, role=self.role)
        self.fields = AlertFields(session=self.session, role=self.role)
    
    async def list_alerts(
        self,
        limit: int | None = None,
        order_by: Literal["created_at", "updated_at", "priority", "severity", "status"]
        | None = None,
        sort: Literal["asc", "desc"] | None = None,
    ) -> Sequence[Alert]:
        statement = select(Alert).where(Alert.owner_id == self.workspace_id)
        if limit is not None:
            statement = statement.limit(limit)
        if order_by is not None:
            attr = getattr(Alert, order_by)
            if sort == "asc":
                statement = statement.order_by(attr.asc())
            elif sort == "desc":
                statement = statement.order_by(attr.desc())
            else:
                statement = statement.order_by(attr)
        result = await self.session.exec(statement)
        return result.all()

    async def list_alerts_paginated(
        self,
        params: CursorPaginationParams,
        search_term: str | None = None,
        status: AlertStatus | None = None,
        priority: AlertPriority | None = None,
        severity: AlertSeverity | None = None,
        tag_ids: list[uuid.UUID] | None = None,
    ) -> CursorPaginatedResponse[AlertReadMinimal]:
        """List alerts with cursor-based pagination and filtering."""
        paginator = BaseCursorPaginator(self.session)

        # Get estimated total count from table statistics
        total_estimate = await paginator.get_table_row_estimate("alerts")

        # Base query with workspace filter - eagerly load tags and assignee
        stmt = (
            select(Alert)
            .where(Alert.owner_id == self.workspace_id)
            .order_by(col(Alert.created_at).desc(), col(Alert.id).desc())
        )

        # Apply search term filter
        if search_term:
            # Validate search term to prevent abuse
            if len(search_term) > 1000:
                raise ValueError("Search term cannot exceed 1000 characters")
            if "\x00" in search_term:
                raise ValueError("Search term cannot contain null bytes")

            # Use SQLAlchemy's concat function for proper parameter binding
            search_pattern = func.concat("%", search_term, "%")
            stmt = stmt.where(
                or_(
                    col(Alert.summary).ilike(search_pattern),
                    col(Alert.description).ilike(search_pattern),
                )
            )

        # Apply status filter
        if status:
            stmt = stmt.where(Alert.status == status)

        # Apply priority filter
        if priority:
            stmt = stmt.where(Alert.priority == priority)

        # Apply severity filter
        if severity:
            stmt = stmt.where(Alert.severity == severity)

        # Apply tag filtering if tag_ids provided (AND logic - case must have all tags)
        if tag_ids:
            for tag_id in tag_ids:
                stmt = stmt.where(
                    col(Alert.id).in_(
                        select(AlertTag.alert_id).where(AlertTag.tag_id == tag_id)
                    )
                )

        # Apply cursor filtering
        if params.cursor:
            cursor_data = paginator.decode_cursor(params.cursor)
            cursor_time = cursor_data.created_at
            cursor_id = uuid.UUID(cursor_data.id)

            if params.reverse:
                stmt = stmt.where(
                    or_(
                        col(Alert.created_at) > cursor_time,
                        and_(
                            col(Alert.created_at) == cursor_time,
                            col(Alert.id) > cursor_id,
                        ),
                    )
                ).order_by(col(Alert.created_at).asc(), col(Alert.id).asc())
            else:
                stmt = stmt.where(
                    or_(
                        col(Alert.created_at) < cursor_time,
                        and_(
                            col(Alert.created_at) == cursor_time,
                            col(Alert.id) < cursor_id,
                        ),
                    )
                )

        # Fetch limit + 1 to determine if there are more items
        stmt = stmt.limit(params.limit + 1)
        result = await self.session.exec(stmt)
        all_alerts = result.all()

        # Check if there are more items
        has_more = len(all_alerts) > params.limit
        alerts = all_alerts[: params.limit] if has_more else all_alerts

        # Generate cursors
        next_cursor = None
        prev_cursor = None
        has_previous = params.cursor is not None

        if has_more and alerts:
            last_alert = alerts[-1]
            next_cursor = paginator.encode_cursor(last_alert.created_at, last_alert.id)

        if params.cursor and alerts:
            first_alert = alerts[0]
            # For reverse pagination, swap the cursor meaning
            if params.reverse:
                next_cursor = paginator.encode_cursor(
                    first_alert.created_at, first_alert.id
                )
            else:
                prev_cursor = paginator.encode_cursor(
                    first_alert.created_at, first_alert.id
                )

        # Convert to CaseReadMinimal objects with tags
        alert_items = []
        for alert in alerts:
            # Tags are already loaded via selectinload
            tag_reads = [
                TagRead.model_validate(tag, from_attributes=True) for tag in alert.tags
            ]

            alert_items.append(
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

        return CursorPaginatedResponse(
            items=alert_items,
            next_cursor=next_cursor,
            prev_cursor=prev_cursor,
            has_more=has_more,
            has_previous=has_previous,
            total_estimate=total_estimate,
        )
    
    async def search_alerts(
        self,
        search_term: str | None = None,
        status: AlertStatus | None = None,
        priority: AlertPriority | None = None,
        severity: AlertSeverity | None = None,
        tag_ids: list[uuid.UUID] | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        updated_before: datetime | None = None,
        updated_after: datetime | None = None,
        order_by: Literal["created_at", "updated_at", "priority", "severity", "status"]
        | None = None,
        sort: Literal["asc", "desc"] | None = None,
        limit: int | None = None,
    ) -> Sequence[Alert]:
        """Search cases based on various criteria.

        Args:
            search_term: Text to search for in case summary and description
            status: Filter by case status
            priority: Filter by case priority
            severity: Filter by case severity
            start_time: Filter by case creation time
            end_time: Filter by case creation time
            updated_before: Filter by case update time
            updated_after: Filter by case update time
            order_by: Field to order the cases by
            sort: Direction to sort (asc or desc)
            limit: Maximum number of cases to return

        Returns:
            Sequence of cases matching the search criteria
        """
        statement = (
            select(Alert)
            .where(Alert.owner_id == self.workspace_id)
            .options(selectinload(Alert.tags))  # type: ignore
        )

        # Apply search term filter (search in summary and description)
        if search_term:
            # Validate search term to prevent abuse
            if len(search_term) > 1000:
                raise ValueError("Search term cannot exceed 1000 characters")
            if "\x00" in search_term:
                raise ValueError("Search term cannot contain null bytes")

            # Use SQLAlchemy's concat function for proper parameter binding
            search_pattern = func.concat("%", search_term, "%")
            statement = statement.where(
                or_(
                    col(Alert.summary).ilike(search_pattern),
                    col(Alert.description).ilike(search_pattern),
                )
            )

        # Apply status filter
        if status:
            statement = statement.where(Alert.status == status)

        # Apply priority filter
        if priority:
            statement = statement.where(Alert.priority == priority)

        # Apply severity filter
        if severity:
            statement = statement.where(Alert.severity == severity)

        # Apply tag filtering if specified (AND logic for multiple tags)
        if tag_ids:
            for tag_id in tag_ids:
                # Self-join for each tag to ensure case has ALL specified tags
                tag_alias = aliased(AlertTag)
                statement = statement.join(
                    tag_alias,
                    and_(tag_alias.alert_id == Alert.id, tag_alias.tag_id == tag_id),
                )

        # Apply date filters
        if start_time:
            statement = statement.where(Alert.created_at >= start_time)
        if end_time:
            statement = statement.where(Alert.created_at <= end_time)
        if updated_after:
            statement = statement.where(Alert.updated_at >= updated_after)
        if updated_before:
            statement = statement.where(Alert.updated_at <= updated_before)

        # Apply limit
        if limit is not None:
            statement = statement.limit(limit)

        # Apply ordering
        if order_by is not None:
            attr = getattr(Alert, order_by)
            if sort == "asc":
                statement = statement.order_by(attr.asc())
            elif sort == "desc":
                statement = statement.order_by(attr.desc())
            else:
                statement = statement.order_by(attr)

        result = await self.session.exec(statement)
        return result.all()

    async def get_alert(self, alert_id: uuid.UUID) -> Alert | None:
        """Get a case with its associated custom fields.

        Args:
            case_id: UUID of the case to retrieve

        Returns:
            Tuple containing the case and its fields (or None if no fields exist)

        Raises:
            TracecatNotFoundError: If the case doesn't exist
        """
        statement = (
            select(Alert)
            .where(
                Alert.owner_id == self.workspace_id,
                Alert.id == alert_id,
            )
            .options(selectinload(Alert.tags))  # type: ignore
        )

        result = await self.session.exec(statement)
        return result.first()

    async def create_alert(self, params: AlertCreate) -> Alert:
        # Create the base case first
        alert = Alert(
            owner_id=self.workspace_id,
            summary=params.summary,
            description=params.description,
            priority=params.priority,
            severity=params.severity,
            status=params.status,
            payload=params.payload,
        )

        self.session.add(alert)
        await self.session.flush()  # Generate case ID

        # If fields are provided, create the fields row
        if params.fields:
            await self.fields.create_field_values(alert, params.fields)

        await self.session.commit()
        # Make sure to refresh the case to get the fields relationship loaded
        await self.session.refresh(alert)
        return alert

    async def update_alert(self, alert: Alert, params: AlertUpdate) -> Alert:
        """Update a case and optionally its custom fields.

        Args:
            case: The case object to update
            params: Optional case update parameters
            fields_data: Optional new field values

        Returns:
            Updated case with fields

        Raises:
            TracecatNotFoundError: If the case has no fields when trying to update fields
        """

        run_ctx = ctx_run.get()
        wf_exec_id = run_ctx.wf_exec_id if run_ctx else None

        # Update case parameters if provided
        set_fields = params.model_dump(exclude_unset=True)

        # Check for status changes
        if new_status := set_fields.pop("status", None):
            old_status = alert.status
            if old_status != new_status:
                alert.status = new_status

        # Check for priority changes
        if new_priority := set_fields.pop("priority", None):
            old_priority = alert.priority
            if old_priority != new_priority:
                alert.priority = new_priority
                
        # Check for severity changes
        if new_severity := set_fields.pop("severity", None):
            old_severity = alert.severity
            if old_severity != new_severity:
                alert.severity = new_severity

        if fields := set_fields.pop("fields", None):
            # If fields was set, we need to update the fields row
            # It must be a dictionary because we validated it in the model
            # Get existing fields
            if not isinstance(fields, dict):
                raise ValueError("Fields must be a dict")

            if alert_fields := alert.fields:
                # Merge existing fields with new fields
                existing_fields = await self.fields.get_fields(alert) or {}
                await self.fields.update_field_values(
                    alert_fields.id, existing_fields | fields
                )
            else:
                # Case has no fields row yet, create one
                existing_fields: dict[str, Any] = {}
                await self.fields.create_field_values(alert, fields)
            diffs = []
            for field, value in fields.items():
                old_value = existing_fields.get(field)
                if old_value != value:
                    diffs.append(FieldDiff(field=field, old=old_value, new=value))

        for key, value in set_fields.items():
            old = getattr(alert, key, None)
            setattr(alert, key, value)
  
        # Commit changes and refresh case
        await self.session.commit()
        await self.session.refresh(alert)
        return alert

    async def delete_alert(self, alert: Alert) -> None:
        """Delete a case and optionally its associated field data.

        Args:
            case: The case object to delete
            delete_fields: Whether to also delete the associated field data
        """
        # No need to record a delete activity - when we delete the case,
        # all related activities will be removed too due to cascade delete.
        # However, this activity could be useful in an audit log elsewhere
        # if system-wide activities are implemented separately.

        await self.session.delete(alert)
        await self.session.commit()

class AlertFieldsService(BaseWorkspaceService):
    service_name = "alert_fields"
    _table = AlertFields.__tablename__
    _schema = "public"

    def __init__(self, session: AsyncSession, role: Role | None = None):
        super().__init__(session, role)
        self.tables = TableEditorService(
            session=self.session,
            role=self.role,
            table_name=self._table,
            schema_name=self._schema
        )
    async def list_fields(
            self,
    ) -> Sequence[sa.engine.interfaces.ReflectedColumn]:
        return await self.tables.get_columns()
    
    async def create_field(
        self,
        params: AlertFieldCreate
    ) -> None:
        params.nullable = True
        await self.editor.create_column(params)
        await self.session.commit()

    async def update_field(
        self,
        field_id: str,
        params: AlertFieldUpdate
    ) -> None:
        await self.editor.update_column(field_id, params)
        await self.session.commit()
    
    async def delete_field(
        self,
        field_id: str
    ) -> None:
        await self.editor.delete_column(field_id)
        await self.session.commit()
    
    async def get_fields(self, alert:Alert) -> dict[str, Any] |None:
        if alert.fields is None:
            return None
        return await self.editor.get_row(alert.fields.id)
    
    async def create_field_values(
        self,
        alert:Alert,
        fields: dict[str, Any]
    ) -> dict[str, Any]:
        alert_fields = AlertFields(alert_id=alert.id)
        self.session.add(alert_fields)
        await self.session.flush()
        try:
            res = await self.editor.update_row(row_id=alert_fields.id, data= fields)
            await self.session.flush()
            return res
        except ProgrammingError as e:
            while cause := e.__cause__:
                e = cause
            if isinstance(cause, UndefinedColumnError):
                raise TracecatException(
                    f"One or more fields do not exist. Details: {cause}"
                ) from e
            raise TracecatException(
                "Failed to create alert fields. Please check the field names and types."
            ) from e
    
    async def update_field_values(self, id: uuid.UUID, fields: dict[str, Any]) -> None:
        """Update a alert field value. Non-transactional.

        Args:
            id: The id of the alert field to update
            fields: The fields to update
        """
        try:
            await self.editor.update_row(id, fields)
        except ProgrammingError as e:
            while cause := e.__cause__:
                e = cause
            if isinstance(e, UndefinedColumnError):
                raise TracecatException(
                    f"Failed to update alert fields. {str(e).replace('relation', 'table').capitalize()}."
                    " Please ensure these fields have been created and try again."
                ) from e
            raise TracecatException(
                f"Unexpected error updating alert fields: {e}"
            ) from e
        
class AlertCommentsService(BaseWorkspaceService):
    service_name = "alert_comments"
    async def get_comment(self, comment_id: uuid.UUID) -> AlertComment | None:
        statement = select(AlertComment).where(
            AlertComment.owner_id == self.workspace_id,
            AlertComment.id == comment_id,
        )
        result = await self.session.exec(statement)
        return result.first()
    
    async def list_comments(
        self, alert: Alert, *, with_users: bool = True
    ) -> list[tuple[AlertComment, User | None]]:
        """List all comments for a case with optional user information.

        Args:
            case: The case to get comments for
            with_users: Whether to include user information (default: True)

        Returns:
            A list of tuples containing comments and their associated users (or None if no user)
        """

        if with_users:
            statement = (
                select(AlertComment, User)
                .outerjoin(User, cast(AlertComment.user_id, sa.UUID) == User.id)
                .where(AlertComment.alert_id == alert.id)
                .order_by(cast(AlertComment.created_at, sa.DateTime))
            )
            result = await self.session.exec(statement)
            return list(result.all())
        else:
            statement = (
                select(AlertComment)
                .where(AlertComment.alert_id == alert.id)
                .order_by(cast(AlertComment.created_at, sa.DateTime))
            )
            result = await self.session.exec(statement)
            # Return in the same format as the join query for consistency
            return [(comment, None) for comment in result.all()]

    async def create_comment(
        self, alert: Alert, params: AlertCommentCreate
    ) -> AlertComment:
        """Create a new comment on a case.

        Args:
            case: The case to comment on
            params: The comment parameters

        Returns:
            The created comment
        """
        comment = AlertComment(
            owner_id=self.workspace_id,
            alert_id=alert.id,
            content=params.content,
            parent_id=params.parent_id,
            user_id=self.role.user_id,
        )

        self.session.add(comment)
        await self.session.commit()
        await self.session.refresh(comment)

        return comment

    async def update_comment(
        self, comment: AlertComment, params: AlertCommentUpdate
    ) -> AlertComment:
        """Update an existing comment.

        Args:
            comment: The comment to update
            params: The updated comment parameters

        Returns:
            The updated comment

        Raises:
            TracecatNotFoundError: If the comment doesn't exist
            TracecatAuthorizationError: If the user doesn't own the comment
        """
        # Check if the user owns the comment
        if comment.user_id != self.role.user_id:
            raise TracecatAuthorizationError("You cannot update this comment")

        set_fields = params.model_dump(exclude_unset=True)
        for key, value in set_fields.items():
            setattr(comment, key, value)

        # Set last_edited_at
        comment.last_edited_at = datetime.now(UTC)

        await self.session.commit()
        await self.session.refresh(comment)

        return comment

    async def delete_comment(self, comment: AlertComment) -> None:
        """Delete a comment.

        Args:
            case: The case the comment belongs to
            comment_id: The ID of the comment to delete

        Raises:
            TracecatNotFoundError: If the comment doesn't exist
            TracecatAuthorizationError: If the user doesn't own the comment
        """

        # Check if the user owns the comment
        if comment.user_id != self.role.user_id:
            raise TracecatAuthorizationError("You can only delete your own comments")

        await self.session.delete(comment)
        await self.session.commit()
