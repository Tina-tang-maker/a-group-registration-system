from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User
from app.models.activity import Activity
from app.models.member import ActivityMember
from app.schemas.identity import CurrentActor


async def check_activity_operator(
    db: AsyncSession, actor: CurrentActor, activity_id: str
) -> bool:
    if not actor.is_operator:
        return False
    from app.models.role_grant import RoleGrant
    result = await db.execute(
        select(RoleGrant).where(
            RoleGrant.user_id == actor.user_id,
            RoleGrant.activity_id == activity_id,
            RoleGrant.role == "OPERATOR",
        )
    )
    if result.scalar_one_or_none():
        return True
    result = await db.execute(
        select(RoleGrant).where(
            RoleGrant.user_id == actor.user_id,
            RoleGrant.activity_id.is_(None),
            RoleGrant.role == "OPERATOR",
            RoleGrant.scope == "GLOBAL",
        )
    )
    return result.scalar_one_or_none() is not None


async def check_member_active(
    db: AsyncSession, user_id: str, activity_id: str, role: str
) -> ActivityMember | None:
    result = await db.execute(
        select(ActivityMember).where(
            ActivityMember.activity_id == activity_id,
            ActivityMember.user_id == user_id,
            ActivityMember.role == role,
            ActivityMember.participation_status == "ACTIVE",
        )
    )
    return result.scalar_one_or_none()


async def get_activity_or_404(db: AsyncSession, activity_id: str) -> Activity:
    result = await db.execute(select(Activity).where(Activity.id == activity_id))
    activity = result.scalar_one_or_none()
    if not activity:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Activity not found")
    return activity
