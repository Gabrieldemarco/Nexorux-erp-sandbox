from fastapi import APIRouter, Depends

from app.core.auth import get_current_user
from app.core.catalog import build_catalog
from app.models.user import User

router = APIRouter()


@router.get("/")
async def get_catalog(_current_user: User = Depends(get_current_user)):
    """Functional catalogs for UI: statuses, CFE types, currency defaults."""
    return build_catalog()
