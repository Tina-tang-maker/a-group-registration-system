from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.member import ActivityMember
from app.models.coverage import CoverageAlert, CoverageReview
from app.models.activity import Activity
from app.schemas.coverage import CoverageAlertView, CoverageReviewInput
from app.schemas.common import Page
from app.schemas.identity import CurrentActor
from app.services.auth import check_activity_operator
from app.dependencies import now_iso
from fastapi import HTTPException


async def run_coverage_analysis(
    db: AsyncSession, actor: CurrentActor, activity_id: str
) -> dict:
    if not await check_activity_operator(db, actor, activity_id):
        raise HTTPException(status_code=403, detail="Operator access required")

    activity_result = await db.execute(select(Activity).where(Activity.id == activity_id))
    activity = activity_result.scalar_one_or_none()
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")

    students_result = await db.execute(
        select(ActivityMember).where(
            ActivityMember.activity_id == activity_id,
            ActivityMember.role == "STUDENT",
            ActivityMember.submission_status == "SUBMITTED",
            ActivityMember.review_status.in_(["PENDING", "APPROVED"]),
            ActivityMember.participation_status == "ACTIVE",
        )
    )
    students = students_result.scalars().all()

    experts_result = await db.execute(
        select(ActivityMember).where(
            ActivityMember.activity_id == activity_id,
            ActivityMember.role == "EXPERT",
            ActivityMember.review_status == "APPROVED",
            ActivityMember.participation_status == "ACTIVE",
        )
    )
    experts = experts_result.scalars().all()

    alerts_created = 0
    for student in students:
        from app.models.registration import RegistrationSnapshot
        snap_result = await db.execute(
            select(RegistrationSnapshot).where(RegistrationSnapshot.id == student.current_submission_id)
        )
        snapshot = snap_result.scalar_one_or_none()
        if not snapshot:
            continue

        content = snapshot.content or {}
        sections = content.get("sections", {})
        has_content = any(v for v in sections.values() if v and len(str(v)) > 10)

        if not has_content:
            alert = CoverageAlert(
                activity_id=activity_id,
                student_member_id=student.id,
                category="INFORMATION_INSUFFICIENT",
                status="OPEN",
                input_roster_version=activity.version,
                need_summary="学员提交的需求资料信息不足，无法进行覆盖分析",
                analyzed_expert_ids=[e.id for e in experts],
                evidence=f"学员 {student.public_display_name} 的三段正文内容过少",
            )
            db.add(alert)
            alerts_created += 1

    from app.models.notification import AuditLog
    db.add(AuditLog(
        activity_id=activity_id,
        actor_user_id=actor.user_id,
        action="COVERAGE_ANALYSIS_RUN",
        target_type="activity",
        target_id=activity_id,
        detail={"alerts_created": alerts_created},
    ))
    return {"alerts_created": alerts_created, "students_analyzed": len(students), "experts_available": len(experts)}


async def list_coverage_alerts(
    db: AsyncSession, actor: CurrentActor, activity_id: str,
    page: int, page_size: int,
    status: str | None = None, category: str | None = None,
) -> Page[CoverageAlertView]:
    if not await check_activity_operator(db, actor, activity_id):
        raise HTTPException(status_code=403, detail="Operator access required")

    query = select(CoverageAlert).where(CoverageAlert.activity_id == activity_id)
    if status:
        query = query.where(CoverageAlert.status == status)
    if category:
        query = query.where(CoverageAlert.category == category)

    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    items_q = query.order_by(CoverageAlert.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(items_q)
    alerts = result.scalars().all()

    items = []
    for alert in alerts:
        reviews_result = await db.execute(
            select(CoverageReview).where(CoverageReview.alert_id == alert.id)
            .order_by(CoverageReview.created_at.asc())
        )
        reviews = [
            {"conclusion": r.conclusion, "reason": r.reason, "reviewer_id": r.reviewer_id, "created_at": r.created_at.isoformat()}
            for r in reviews_result.scalars().all()
        ]
        items.append(CoverageAlertView(
            id=alert.id,
            activity_id=alert.activity_id,
            student_member_id=alert.student_member_id,
            category=alert.category,
            status=alert.status,
            input_roster_version=alert.input_roster_version,
            need_summary=alert.need_summary,
            missing_tags=alert.missing_tags,
            analyzed_expert_ids=alert.analyzed_expert_ids,
            evidence=alert.evidence,
            reviews=reviews,
        ))

    return Page(items=items, total=total, page=page, page_size=page_size)


async def add_coverage_review(
    db: AsyncSession, actor: CurrentActor, activity_id: str,
    alert_id: str, data: CoverageReviewInput
) -> CoverageAlertView:
    if not await check_activity_operator(db, actor, activity_id):
        raise HTTPException(status_code=403, detail="Operator access required")

    result = await db.execute(
        select(CoverageAlert).where(
            CoverageAlert.id == alert_id,
            CoverageAlert.activity_id == activity_id,
        )
    )
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    if alert.input_roster_version != data.expected_version:
        raise HTTPException(status_code=409, detail="Version conflict")

    review = CoverageReview(
        alert_id=alert.id,
        conclusion=data.conclusion,
        reason=data.reason,
        reviewer_id=actor.user_id,
        input_version=alert.input_roster_version,
    )
    db.add(review)

    if data.conclusion == "RESOLVED":
        alert.status = "RESOLVED"

    from app.models.notification import AuditLog
    db.add(AuditLog(
        activity_id=activity_id,
        actor_user_id=actor.user_id,
        action="COVERAGE_REVIEW_ADDED",
        target_type="coverage_alert",
        target_id=alert.id,
        detail={"conclusion": data.conclusion},
    ))

    reviews_result = await db.execute(
        select(CoverageReview).where(CoverageReview.alert_id == alert.id)
        .order_by(CoverageReview.created_at.asc())
    )
    reviews = [
        {"conclusion": r.conclusion, "reason": r.reason, "reviewer_id": r.reviewer_id, "created_at": r.created_at.isoformat()}
        for r in reviews_result.scalars().all()
    ]
    return CoverageAlertView(
        id=alert.id,
        activity_id=alert.activity_id,
        student_member_id=alert.student_member_id,
        category=alert.category,
        status=alert.status,
        input_roster_version=alert.input_roster_version,
        need_summary=alert.need_summary,
        missing_tags=alert.missing_tags,
        analyzed_expert_ids=alert.analyzed_expert_ids,
        evidence=alert.evidence,
        reviews=reviews,
    )
