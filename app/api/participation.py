from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.dependencies import require_operator
from app.schemas.identity import CurrentActor
from app.schemas.manual import CapacityUpdateInput, CapacityUpdateView, MemberParticipationChanged
from app.services.participation import update_expert_capacity, end_participation, withdraw_member

router = APIRouter(prefix="/api/v1/activities/{activity_id}", tags=["participation"])


@router.patch("/members/{member_id}/capacity", response_model=CapacityUpdateView)
async def update_capacity(
    activity_id: str,
    member_id: str,
    data: CapacityUpdateInput,
    actor: CurrentActor = Depends(require_operator),
    db: AsyncSession = Depends(get_db),
):
    return await update_expert_capacity(db, actor, activity_id, member_id, data)


@router.post("/members/{member_id}/end", response_model=MemberParticipationChanged)
async def end_member(
    activity_id: str,
    member_id: str,
    data: dict,
    actor: CurrentActor = Depends(require_operator),
    db: AsyncSession = Depends(get_db),
):
    return await end_participation(db, actor, activity_id, member_id, data.get("reason", ""))


@router.post("/members/{member_id}/withdraw", response_model=MemberParticipationChanged)
async def withdraw(
    activity_id: str,
    member_id: str,
    data: dict,
    actor: CurrentActor = Depends(require_operator),
    db: AsyncSession = Depends(get_db),
):
    return await withdraw_member(db, actor, activity_id, member_id, data.get("reason", ""))
