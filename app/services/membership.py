from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.member import ActivityMember, MemberContact
from app.models.activity import Activity
from app.schemas.registration import JoinInput
from app.schemas.identity import CurrentActor
from app.dependencies import now_iso
from fastapi import HTTPException


async def join_activity(
    db: AsyncSession, actor: CurrentActor, activity_id: str, data: JoinInput
) -> dict:
    result = await db.execute(select(Activity).where(Activity.id == activity_id))
    activity = result.scalar_one_or_none()
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    if activity.status != "PUBLISHED":
        raise HTTPException(status_code=409, detail="Activity is not open for registration")

    existing = await db.execute(
        select(ActivityMember).where(
            ActivityMember.activity_id == activity_id,
            ActivityMember.user_id == actor.user_id,
            ActivityMember.role == data.role,
        )
    )
    member = existing.scalar_one_or_none()
    if member:
        return {"activity_member_id": member.id, "created": False}

    count_result = await db.execute(
        select(ActivityMember).where(
            ActivityMember.activity_id == activity_id,
            ActivityMember.role == data.role,
        )
    )
    seq = len(count_result.scalars().all()) + 1
    prefix = "学员" if data.role == "STUDENT" else "专家"
    display_name = f"{prefix} {seq:02d}"

    member = ActivityMember(
        activity_id=activity_id,
        user_id=actor.user_id,
        role=data.role,
        public_display_name=display_name,
        submission_status="DRAFT",
        review_status="NOT_SUBMITTED",
        participation_status="ACTIVE",
        version=1,
    )
    db.add(member)
    await db.flush()

    from app.models.registration import RegistrationDraft
    draft = RegistrationDraft(
        activity_member_id=member.id,
        role=data.role,
        basic={},
        sections={},
        structured={},
    )
    db.add(draft)

    from app.models.notification import AuditLog
    db.add(AuditLog(
        activity_id=activity_id,
        actor_user_id=actor.user_id,
        action="MEMBER_JOINED",
        target_type="activity_member",
        target_id=member.id,
        detail={"role": data.role},
    ))
    return {"activity_member_id": member.id, "created": True}
