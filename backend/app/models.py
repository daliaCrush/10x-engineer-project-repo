"""Pydantic models for PromptLab."""

from datetime import datetime
from typing import List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator

def generate_id() -> str:
    """Generate a unique resource identifier.

    Returns:
        A UUID represented as a string.
    """
    return str(uuid4())

def get_current_time() -> datetime:
    """Return the current UTC date and time.

    Returns:
        The current UTC date and time.
    """
    return datetime.utcnow()


# ============== Prompt Models ==============


class PromptBase(BaseModel):
    """Shared fields for prompt models."""

    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)
    description: Optional[str] = Field(None, max_length=500)
    collection_id: Optional[str] = None


class PromptCreate(PromptBase):
    """Request model for creating a prompt."""

    pass


class PromptUpdate(PromptBase):
    """Request model for replacing a prompt."""

    pass


class PromptPatch(BaseModel):
    """Request model for partially updating a prompt."""

    title: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=200,
    )
    content: Optional[str] = Field(
        default=None,
        min_length=1,
    )
    description: Optional[str] = Field(
        default=None,
        max_length=500,
    )
    collection_id: Optional[str] = None

    @field_validator("title", "content")
    @classmethod
    def reject_null_required_fields(
        cls,
        value: Optional[str],
    ) -> str:
        """Reject explicit null values for required prompt fields.

        Args:
            value: Explicitly supplied title or content value.

        Returns:
            The validated non-null string.

        Raises:
            ValueError: If the field was explicitly supplied as null.
        """
        if value is None:
            raise ValueError("Field cannot be null")

        return value


class Prompt(PromptBase):
    """Stored prompt model."""

    id: str = Field(default_factory=generate_id)
    created_at: datetime = Field(default_factory=get_current_time)
    updated_at: datetime = Field(default_factory=get_current_time)

    class Config:
        """Pydantic configuration."""

        from_attributes = True


# ============== Collection Models ==============


class CollectionBase(BaseModel):
    """Shared fields for collection models."""

    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)


class CollectionCreate(CollectionBase):
    """Request model for creating a collection."""

    pass


class Collection(CollectionBase):
    """Stored collection model."""

    id: str = Field(default_factory=generate_id)
    created_at: datetime = Field(default_factory=get_current_time)

    class Config:
        """Pydantic configuration."""

        from_attributes = True


# ============== Response Models ==============


class PromptList(BaseModel):
    """Response model containing prompts and their total count."""

    prompts: List[Prompt]
    total: int


class CollectionList(BaseModel):
    """Response model containing collections and their total count."""

    collections: List[Collection]
    total: int


class HealthResponse(BaseModel):
    """Response model for the health endpoint."""

    status: str
    version: str