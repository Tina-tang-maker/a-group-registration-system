from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.dependencies import get_current_actor, require_operator, pagination
from app.schemas.identity import CurrentActor
from app.schemas.activity import ActivityCreate, ActivityPatch, ActivityView, ActivitySummary, VersionInput
from app.schemas.common import Page
from app.services.activity import (
    create_activity, list_activities, get_activity,
    patch_activity, publish_activity,
)

router = APIRouter(prefix="/api/v1/activities", tags=["activities"])


@router.get("", response_model=Page[ActivitySummary])
async def list_acts(
    page: int = 1, page_size: int = 20,
    actor: CurrentActor = Depends(get_current_actor),
    db: AsyncSession = Depends(get_db),
):
    return await list_activities(db, actor, page, page_size)


@router.post("", response_model=ActivityView, status_code=201)
async def create_act(
    data: ActivityCreate,
    actor: CurrentActor = Depends(require_operator),
    db: AsyncSession = Depends(get_db),
):
    return await create_activity(db, actor, data)


@router.get("/{activity_id}", response_model=ActivityView)
async def get_act(
    activity_id: str,
    actor: CurrentActor = Depends(get_current_actor),
    db: AsyncSession = Depends(get_db),
):
    return await get_activity(db, actor, activity_id)


@router.patch("/{activity_id}", response_model=ActivityView)
async def patch_act(
    activity_id: str,
    data: ActivityPatch,
    actor: CurrentActor = Depends(require_operator),
    db: AsyncSession = Depends(get_db),
):
    return await patch_activity(db, actor, activity_id, data)


@router.post("/{activity_id}/publication", response_model=ActivityView)
async def publish_act(
    activity_id: str,
    data: VersionInput,
    actor: CurrentActor = Depends(require_operator),
    db: AsyncSession = Depends(get_db),
):
    return await publish_activity(db, actor, activity_id, data.expected_version)
