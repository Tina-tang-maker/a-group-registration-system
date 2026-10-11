from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.member import ActivityMember
from app.models.notification import Notification
from app.models.activity import Activity
from app.schemas.notification import NotificationView, ReminderInput, ReminderResult
from app.schemas.common import Page
from app.schemas.identity import CurrentActor
from app.services.auth import check_activity_operator
from app.dependencies import now_iso
from fastapi import HTTPException


async def list_notifications(
    db: AsyncSession, actor: CurrentActor, page: int, page_size: int
) -> Page[NotificationView]:
    query = select(Notification).where(Notification.user_id == actor.user_id)
    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    items_q = query.order_by(Notification.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(items_q)
    notifications = result.scalars().all()

    items = [
        NotificationView(
            id=n.id,
            activity_id=n.activity_id,
            notification_type=n.notification_type,
            title=n.title,
            body=n.body,
            target_id=n.target_id,
            is_read=n.is_read,
            read_at=n.read_at,
            created_at=n.created_at.isoformat(),
        )
        for n in notifications
    ]
    return Page(items=items, total=total, page=page, page_size=page_size)


async def mark_read(
    db: AsyncSession, actor: CurrentActor, notification_id: str
) -> NotificationView:
    result = await db.execute(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == actor.user_id,
        )
    )
    notification = result.scalar_one_or_none()
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    if not notification.is_read:
        notification.is_read = True
        notification.read_at = now_iso()

    return NotificationView(
        id=notification.id,
        activity_id=notification.activity_id,
        notification_type=notification.notification_type,
        title=notification.title,
        body=notification.body,
        target_id=notification.target_id,
        is_read=notification.is_read,
        read_at=notification.read_at,
        created_at=notification.created_at.isoformat(),
    )


async def send_reminders(
    db: AsyncSession, actor: CurrentActor, activity_id: str, data: ReminderInput
) -> ReminderResult:
    if not await check_activity_operator(db, actor, activity_id):
        raise HTTPException(status_code=403, detail="Operator access required")

    activity_result = await db.execute(select(Activity).where(Activity.id == activity_id))
    activity = activity_result.scalar_one_or_none()
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")

    created = 0
    deduplicated = 0
    rejected = 0
    rejection_reasons = []

    unique_ids = list(set(data.member_ids))

    for member_id in unique_ids:
        member_result = await db.execute(
            select(ActivityMember).where(
                ActivityMember.id == member_id,
                ActivityMember.activity_id == activity_id,
            )
        )
        member = member_result.scalar_one_or_none()
        if not member:
            rejected += 1
            rejection_reasons.append(f"Member {member_id} not found")
            continue
        if member.participation_status != "ACTIVE":
            rejected += 1
            rejection_reasons.append(f"Member {member_id} is not active")
            continue
        if member.submission_status != "DRAFT":
            rejected += 1
            rejection_reasons.append(f"Member {member_id} has already submitted")
            continue

        existing = await db.execute(
            select(Notification).where(
                Notification.user_id == member.user_id,
                Notification.activity_id == activity_id,
                Notification.notification_type == f"REMINDER_{data.template}",
            )
        )
        if existing.scalar_one_or_none():
            deduplicated += 1
            continue

        notification = Notification(
            user_id=member.user_id,
            activity_id=activity_id,
            notification_type=f"REMINDER_{data.template}",
            title="报名提醒",
            body=f"您有一期活动报名尚未完成，请尽快提交",
            target_id=member.id,
        )
        db.add(notification)
        created += 1

    return ReminderResult(
        created=created,
        deduplicated=deduplicated,
        rejected=rejected,
        rejection_reasons=rejection_reasons,
    )
