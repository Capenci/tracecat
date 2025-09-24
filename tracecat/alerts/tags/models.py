from pydantic import BaseModel, Field

from tracecat.identifiers import TagID

TagIdentifier = TagID | str  # Can be UUID or ref


class AlertTagCreate(BaseModel):
    tag_id: TagIdentifier = Field(
        description="Tag ID (UUID) or ref",
        min_length=1,
        max_length=100,
    )


class AlertTagRead(BaseModel):
    """Tag data."""

    id: TagID
    name: str
    ref: str
    color: str | None
