from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.member import ActivityMember
from app.models.activity import Activity
from app.models.expert import ExpertParticipation
from app.models.notification import AuditLog, OutboxEvent
from app.schemas.identity import CurrentActor
from app.schemas.manual import CapacityUpdateInput, CapacityUpdateView, MemberParticipationChanged
from app.dependencies import now_iso
from fastapi import HTTPException


async def update_expert_capacity(
    db: AsyncSession, actor: CurrentActor, activity_id: str, member_id: str, data: CapacityUpdateInput
) -> CapacityUpdateView:
    activity_result = await db.execute(select(Activity).where(Activity.id == activity_id))
    activity = activity_result.scalar_one_or_none()
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")

    member_result = await db.execute(
        select(ActivityMember).where(
            ActivityMember.id == member_id,
            ActivityMember.activity_id == activity_id,
            ActivityMember.role == "EXPERT",
        )
    )
    member = member_result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=404, detail="Expert member not found")

    part_result = await db.execute(
        select(ExpertParticipation).where(ExpertParticipation.activity_member_id == member_id)
    )
    part = part_result.scalar_one_or_none()
    if not part:
        raise HTTPException(status_code=404, detail="Expert participation not found")

    if part.version != data.expected_version:
        raise HTTPException(status_code=409, detail="Version conflict")

    if data.capacity_override is not None and data.capacity_override < 0:
        raise HTTPException(status_code=422, detail="Capacity override must be non-negative")

    effective_capacity = data.capacity_override if data.capacity_override is not None else activity.capacity_max

    old_value = part.capacity_override
    part.capacity_override = data.capacity_override
    part.version += 1

    db.add(AuditLog(
        activity_id=activity_id,
        actor_user_id=actor.user_id,
        action="EXPERT_CAPACITY_UPDATED",
        target_type="expert_participation",
        target_id=part.id,
        detail={
            "activity_member_id": member_id,
            "old_capacity_override": old_value,
            "new_capacity_override": data.capacity_override,
            "effective_capacity": effective_capacity,
            "reason": data.reason,
        },
    ))

    return CapacityUpdateView(
        activity_member_id=member_id,
        capacity_override=data.capacity_override,
        effective_capacity=effective_capacity,
        version=part.version,
    )


async def end_participation(
    db: AsyncSession, actor: CurrentActor, activity_id: str, member_id: str, reason: str
) -> MemberParticipationChanged:
    member_result = await db.execute(
        select(ActivityMember).where(
            ActivityMember.id == member_id,
            ActivityMember.activity_id == activity_id,
        )
    )
    member = member_result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    if member.participation_status not in ["ACTIVE"]:
        raise HTTPException(status_code=409, detail=f"Member is {member.participation_status}, cannot end")

    previous_status = member.participation_status
    member.participation_status = "INACTIVE"
    member.version += 1

    event = MemberParticipationChanged(
        activity_id=activity_id,
        activity_member_id=member_id,
        role=member.role,
        previous_status=previous_status,
        participation_status="INACTIVE",
        reason=reason,
        changed_at=now_iso(),
    )

    db.add(AuditLog(
        activity_id=activity_id,
        actor_user_id=actor.user_id,
        action="PARTICIPATION_ENDED",
        target_type="activity_member",
        target_id=member_id,
        detail={"reason": reason, "previous_status": previous_status},
    ))

    db.add(OutboxEvent(
        event_type="MEMBER_PARTICIPATION_CHANGED",
        activity_id=activity_id,
        payload=event.model_dump(),
    ))

    return event


async def withdraw_member(
    db: AsyncSession, actor: CurrentActor, activity_id: str, member_id: str, reason: str
) -> MemberParticipationChanged:
    member_result = await db.execute(
        select(ActivityMember).where(
            ActivityMember.id == member_id,
            ActivityMember.activity_id == activity_id,
        )
    )
    member = member_result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    if member.participation_status != "ACTIVE":
        raise HTTPException(status_code=409, detail=f"Member is {member.participation_status}, cannot withdraw")

    previous_status = member.participation_status
    member.participation_status = "WITHDRAWN"
    member.version += 1

    event = MemberParticipationChanged(
        activity_id=activity_id,
        activity_member_id=member_id,
        role=member.role,
        previous_status=previous_status,
        participation_status="WITHDRAWN",
        reason=reason,
        changed_at=now_iso(),
    )

    db.add(AuditLog(
        activity_id=activity_id,
        actor_user_id=actor.user_id,
        action="MEMBER_WITHDRAWN",
        target_type="activity_member",
        target_id=member_id,
        detail={"reason": reason, "previous_status": previous_status},
    ))

    db.add(OutboxEvent(
        event_type="MEMBER_PARTICIPATION_CHANGED",
        activity_id=activity_id,
        payload=event.model_dump(),
    ))

    return event
