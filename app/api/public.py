from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.dependencies import pagination
from app.schemas.activity import PublicActivitySummary
from app.schemas.common import Page
from app.services.activity import list_public_activities

router = APIRouter(prefix="/api/v1/public", tags=["public"])


@router.get("/activities", response_model=Page[PublicActivitySummary])
async def get_public_activities(
    page: int = 1, page_size: int = 20,
    db: AsyncSession = Depends(get_db),
):
    return await list_public_activities(db, page, page_size)
