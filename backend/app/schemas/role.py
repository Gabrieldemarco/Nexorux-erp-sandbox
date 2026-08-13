from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from uuid import UUID
from datetime import datetime


class RoleBase(BaseModel):
    """Base role schema."""
    name: str = Field(..., min_length=1, max_length=100)
    key: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    is_default: bool = False


class RoleCreate(RoleBase):
    """Schema for creating a role."""
    tenant_id: UUID
    permission_ids: Optional[List[UUID]] = None


class RoleUpdate(BaseModel):
    """Schema for updating a role."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    key: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    is_default: Optional[bool] = None
    permission_ids: Optional[List[UUID]] = None


class RolePermissionBrief(BaseModel):
    id: UUID
    code: str
    name: str

    model_config = ConfigDict(from_attributes=True)


class RoleResponse(RoleBase):
    """Schema for role response."""
    id: UUID
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime
    permissions: List[RolePermissionBrief] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class RolePermissionsUpdate(BaseModel):
    """Replace the full permission set for a role."""
    permission_ids: List[UUID] = Field(default_factory=list)
