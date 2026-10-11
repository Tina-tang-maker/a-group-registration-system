from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.dependencies import require_operator
from app.schemas.identity import CurrentActor
from app.schemas.manual import ManualExpertInput, ManualDraftPatch, ManualSubmitInput
from app.services.manual import create_manual_expert, patch_manual_draft, submit_manual_expert

router = APIRouter(prefix="/api/v1/manual", tags=["manual"])


@router.post("/activities/{activity_id}/experts", status_code=201)
async def create_expert(
    activity_id: str,
    data: ManualExpertInput,
    actor: CurrentActor = Depends(require_operator),
    db: AsyncSession = Depends(get_db),
):
    member = await create_manual_expert(db, actor, activity_id, data)
    return {"activity_member_id": member.id, "user_id": member.user_id, "role": member.role}


@router.patch("/activities/{activity_id}/members/{member_id}/draft")
async def patch_draft(
    activity_id: str,
    member_id: str,
    data: ManualDraftPatch,
    actor: CurrentActor = Depends(require_operator),
    db: AsyncSession = Depends(get_db),
):
    return await patch_manual_draft(db, actor, activity_id, member_id, data)


@router.post("/activities/{activity_id}/members/{member_id}/submit")
async def submit_expert(
    activity_id: str,
    member_id: str,
    data: ManualSubmitInput,
    actor: CurrentActor = Depends(require_operator),
    db: AsyncSession = Depends(get_db),
):
    return await submit_manual_expert(db, actor, activity_id, member_id, data)
