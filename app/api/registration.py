from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.dependencies import get_current_actor, pagination
from app.schemas.identity import CurrentActor
from app.schemas.registration import (
    JoinInput, DraftPatch, SubmitInput, RegistrationView,
    HistoryCopyInput, ReasonInput, SnapshotView,
)
from app.schemas.common import Page
from app.services.membership import join_activity
from app.services.registration import (
    get_registration, patch_draft, submit_registration, withdraw_registration,
)

router = APIRouter(prefix="/api/v1/activities/{activity_id}", tags=["registration"])


@router.post("/memberships")
async def join(
    activity_id: str,
    data: JoinInput,
    actor: CurrentActor = Depends(get_current_actor),
    db: AsyncSession = Depends(get_db),
):
    return await join_activity(db, actor, activity_id, data)


@router.get("/me/registration", response_model=RegistrationView)
async def get_reg(
    activity_id: str,
    actor: CurrentActor = Depends(get_current_actor),
    db: AsyncSession = Depends(get_db),
):
    return await get_registration(db, actor, activity_id)


@router.patch("/me/registration/draft", response_model=RegistrationView)
async def patch_reg_draft(
    activity_id: str,
    data: DraftPatch,
    actor: CurrentActor = Depends(get_current_actor),
    db: AsyncSession = Depends(get_db),
):
    return await patch_draft(db, actor, activity_id, data)


@router.post("/me/registration/submissions", response_model=RegistrationView)
async def submit_reg(
    activity_id: str,
    data: SubmitInput,
    actor: CurrentActor = Depends(get_current_actor),
    db: AsyncSession = Depends(get_db),
):
    return await submit_registration(db, actor, activity_id, data.confirmed)


@router.post("/me/registration/withdrawal", response_model=RegistrationView)
async def withdraw_reg(
    activity_id: str,
    data: ReasonInput,
    actor: CurrentActor = Depends(get_current_actor),
    db: AsyncSession = Depends(get_db),
):
    return await withdraw_registration(db, actor, activity_id, data.reason)
