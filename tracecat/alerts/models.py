from __future__ import annotations

import uuid
from datetime import datetime
from typing import Annotated, Any, Literal

import sqlalchemy as sa
from pydantic import BaseModel, Field, RootModel

from tracecat.auth.models import UserRead
from tracecat.alerts.enums import AlertStatus, AlertSeverity, AlertPriority
from tracecat.tables.enums import SqlType
from tracecat.tables.models import TableColumnCreate, TableColumnUpdate
from tracecat.tags.models import TagRead

class AlertReadMinimal(BaseModel):
    id: uuid.UUID
    short_id: str
    created_at: datetime
    updated_at: datetime
    title: str
    status: AlertStatus
    priority: AlertPriority
    severity: AlertSeverity
    tags: list[TagRead] = Field(default_factory=list)

class AlertRead(BaseModel):
    id: uuid.UUID
    short_id: str
    created_at: datetime
    updated_at: datetime
    summary: str
    status: AlertStatus
    priority: AlertPriority
    severity: AlertSeverity
    description: str
    fields: list[AlertCustomFieldRead]
    payload: dict[str, Any] | None
    tags: list[TagRead] = Field(default_factory=list)

class AlertCreate(BaseModel):
    summary: str
    description: str
    status: AlertStatus
    priority: AlertPriority
    severity: AlertSeverity
    fields: dict[str, Any] | None = None
    payload: dict[str, Any] | None = None

class AlertUpdate(BaseModel):
    summary: str | None = None
    description: str | None = None
    status: AlertStatus | None = None
    priority: AlertPriority | None = None
    severity: AlertSeverity | None = None
    fields: dict[str, Any] | None = None
    payload: dict[str, Any] | None = None

# Alert Fields

class AlertFieldRead(BaseModel):
    
    
    id :str
    type :SqlType
    description :str | None
    nullable :bool
    default :str | None

    @staticmethod
    def from_sa(
        column: sa.engine.interfaces.ReflectedColumn,
    ) -> AlertFieldRead:
        return AlertFieldRead(
            id=column.name,
            type=SqlType(column.type.__class__.__name__.upper()),
            description=column.comment,
            nullable=column.nullable,
            default=str(column.default.arg) if column.default is not None else None,
        )
    
class AlertFieldCreate(TableColumnCreate):
    """Create model for an alert field."""

class AlertFieldUpdate(TableColumnUpdate):
    """Update model for an alert field."""

class AlertCustomFieldRead(BaseModel):
    value: Any
        
# Alert Comments

class AlertCommentRead(BaseModel):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    content: str
    parent_id: uuid.UUID | None = None
    user: UserRead | None = None
    last_edited_at: datetime | None = None

class AlertCommentCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=5_000)
    parent_id: uuid.UUID | None = Field(default=None)

class AlertCommentUpdate(BaseModel):
    content: str = Field(..., min_length=1, max_length=5_000)
    parent_id: uuid.UUID | None = Field(default=None)

class FieldDiff(BaseModel):
    field: str
    old: Any
    new: Any




