from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.member import ActivityMember
from app.models.notification import AuditLog
from app.models.activity import Activity
from app.schemas.audit import AuditView, DashboardView
from app.schemas.common import Page
from app.schemas.identity import CurrentActor
from app.services.auth import check_activity_operator
from fastapi import HTTPException
import csv
import io


async def get_dashboard(
    db: AsyncSession, actor: CurrentActor, activity_id: str
) -> DashboardView:
    if not await check_activity_operator(db, actor, activity_id):
        raise HTTPException(status_code=403, detail="Operator access required")

    members_q = select(ActivityMember).where(ActivityMember.activity_id == activity_id)
    members_result = await db.execute(members_q)
    members = members_result.scalars().all()

    total = len(members)
    students = sum(1 for m in members if m.role == "STUDENT")
    experts = sum(1 for m in members if m.role == "EXPERT")
    submitted = sum(1 for m in members if m.submission_status == "SUBMITTED")
    pending = sum(1 for m in members if m.review_status == "PENDING")
    approved = sum(1 for m in members if m.review_status == "APPROVED")
    rejected = sum(1 for m in members if m.review_status == "REJECTED")
    active = sum(1 for m in members if m.participation_status == "ACTIVE")
    withdrawn = sum(1 for m in members if m.participation_status == "WITHDRAWN")
    inactive = sum(1 for m in members if m.participation_status == "INACTIVE")

    activity_result = await db.execute(select(Activity).where(Activity.id == activity_id))
    activity = activity_result.scalar_one()

    return DashboardView(
        activity_id=activity_id,
        total_members=total,
        total_students=students,
        total_experts=experts,
        submitted=submitted,
        pending_review=pending,
        approved=approved,
        rejected=rejected,
        active=active,
        withdrawn=withdrawn,
        inactive=inactive,
        expert_capacity_total=experts * activity.capacity_max,
    )


async def list_audit_logs(
    db: AsyncSession, actor: CurrentActor, activity_id: str,
    page: int, page_size: int,
    action: str | None = None,
) -> Page[AuditView]:
    if not await check_activity_operator(db, actor, activity_id):
        raise HTTPException(status_code=403, detail="Operator access required")

    query = select(AuditLog).where(AuditLog.activity_id == activity_id)
    if action:
        query = query.where(AuditLog.action == action)

    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    items_q = query.order_by(AuditLog.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(items_q)
    logs = result.scalars().all()

    items = [
        AuditView(
            id=log.id,
            activity_id=log.activity_id,
            actor_user_id=log.actor_user_id,
            action=log.action,
            target_type=log.target_type,
            target_id=log.target_id,
            detail=log.detail,
            created_at=log.created_at.isoformat(),
        )
        for log in logs
    ]
    return Page(items=items, total=total, page=page, page_size=page_size)


async def export_csv(
    db: AsyncSession, actor: CurrentActor, activity_id: str,
    role: str | None = None, review_status: str | None = None,
) -> str:
    if not await check_activity_operator(db, actor, activity_id):
        raise HTTPException(status_code=403, detail="Operator access required")

    query = select(ActivityMember).where(ActivityMember.activity_id == activity_id)
    if role:
        query = query.where(ActivityMember.role == role)
    if review_status:
        query = query.where(ActivityMember.review_status == review_status)

    result = await db.execute(query)
    members = result.scalars().all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["成员ID", "用户ID", "角色", "显示名称", "提交状态", "审核状态", "参与状态"])

    for m in members:
        writer.writerow([
            m.id, m.user_id, m.role, m.public_display_name,
            m.submission_status, m.review_status, m.participation_status,
        ])

    from app.models.notification import AuditLog as AL
    db.add(AL(
        activity_id=activity_id,
        actor_user_id=actor.user_id,
        action="CSV_EXPORTED",
        target_type="activity",
        target_id=activity_id,
        detail={"row_count": len(members)},
    ))
    return output.getvalue()
