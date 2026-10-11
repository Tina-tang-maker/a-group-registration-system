from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.activity import Activity
from app.schemas.activity import (
    ActivityCreate, ActivityPatch, ActivityView, ActivitySummary,
    PublicActivitySummary,
)
from app.schemas.common import Page
from app.services.auth import check_activity_operator
from app.schemas.identity import CurrentActor
from app.dependencies import now_iso
from fastapi import HTTPException


def _to_view(a: Activity) -> ActivityView:
    return ActivityView(
        activity_id=a.id,
        name=a.name,
        description=a.description,
        status=a.status,
        registration_starts_at=a.registration_starts_at,
        registration_deadline=a.registration_deadline,
        student_choice_starts_at=a.student_choice_starts_at,
        student_choice_deadline=a.student_choice_deadline,
        expert_selection_starts_at=a.expert_selection_starts_at,
        expert_response_deadline=a.expert_response_deadline,
        supplement_choice_starts_at=a.supplement_choice_starts_at,
        supplement_choice_deadline=a.supplement_choice_deadline,
        max_choices_per_student=a.max_choices_per_student,
        capacity_max=a.capacity_max,
        version=a.version,
    )


def _validate_time_order(a: Activity) -> list[str]:
    errors = []
    times = {
        "registration_starts_at": a.registration_starts_at,
        "registration_deadline": a.registration_deadline,
        "student_choice_starts_at": a.student_choice_starts_at,
        "student_choice_deadline": a.student_choice_deadline,
        "expert_selection_starts_at": a.expert_selection_starts_at,
        "expert_response_deadline": a.expert_response_deadline,
        "supplement_choice_starts_at": a.supplement_choice_starts_at,
        "supplement_choice_deadline": a.supplement_choice_deadline,
    }
    if any(v is None for v in times.values()):
        errors.append("All time fields are required for publication")
        return errors

    order = [
        ("registration_starts_at", "registration_deadline"),
        ("registration_deadline", "student_choice_starts_at"),
        ("student_choice_starts_at", "student_choice_deadline"),
        ("student_choice_deadline", "expert_selection_starts_at"),
        ("expert_selection_starts_at", "expert_response_deadline"),
        ("expert_response_deadline", "supplement_choice_starts_at"),
        ("supplement_choice_starts_at", "supplement_choice_deadline"),
    ]
    for before, after in order:
        if times[before] >= times[after]:
            errors.append(f"{before} must be before {after}")
    return errors


async def create_activity(
    db: AsyncSession, actor: CurrentActor, data: ActivityCreate
) -> ActivityView:
    if not actor.is_operator:
        raise HTTPException(status_code=403, detail="Only operators can create activities")

    activity = Activity(
        name=data.name,
        description=data.description,
        status="DRAFT",
        version=1,
    )
    db.add(activity)
    await db.flush()

    from app.models.notification import AuditLog
    db.add(AuditLog(
        activity_id=activity.id,
        actor_user_id=actor.user_id,
        action="ACTIVITY_CREATED",
        target_type="activity",
        target_id=activity.id,
    ))
    return _to_view(activity)


async def list_activities(
    db: AsyncSession, actor: CurrentActor, page: int, page_size: int
) -> Page[ActivitySummary]:
    query = select(Activity)
    if not actor.is_operator:
        query = query.where(Activity.status.in_(["PUBLISHED", "CLOSED"]))

    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    items_q = query.order_by(Activity.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(items_q)
    activities = result.scalars().all()

    items = [
        ActivitySummary(
            activity_id=a.id,
            name=a.name,
            status=a.status,
            registration_starts_at=a.registration_starts_at,
            registration_deadline=a.registration_deadline,
            version=a.version,
        )
        for a in activities
    ]
    return Page(items=items, total=total, page=page, page_size=page_size)


async def list_public_activities(
    db: AsyncSession, page: int, page_size: int
) -> Page[PublicActivitySummary]:
    query = select(Activity).where(Activity.status == "PUBLISHED")
    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    items_q = query.order_by(Activity.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(items_q)
    activities = result.scalars().all()

    items = [
        PublicActivitySummary(
            activity_id=a.id,
            name=a.name,
            description=a.description,
            registration_starts_at=a.registration_starts_at,
            registration_deadline=a.registration_deadline,
        )
        for a in activities
    ]
    return Page(items=items, total=total, page=page, page_size=page_size)


async def get_activity(
    db: AsyncSession, actor: CurrentActor, activity_id: str
) -> ActivityView:
    result = await db.execute(select(Activity).where(Activity.id == activity_id))
    activity = result.scalar_one_or_none()
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    if activity.status == "DRAFT" and not await check_activity_operator(db, actor, activity_id):
        raise HTTPException(status_code=404, detail="Activity not found")
    return _to_view(activity)


async def patch_activity(
    db: AsyncSession, actor: CurrentActor, activity_id: str, data: ActivityPatch
) -> ActivityView:
    if not await check_activity_operator(db, actor, activity_id):
        raise HTTPException(status_code=403, detail="Operator access required")

    result = await db.execute(select(Activity).where(Activity.id == activity_id))
    activity = result.scalar_one_or_none()
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    if activity.status in ("CLOSED",):
        raise HTTPException(status_code=409, detail="Cannot modify closed activity")
    if activity.version != data.expected_version:
        raise HTTPException(status_code=409, detail="Version conflict")

    if data.name is not None:
        activity.name = data.name
    if data.description is not None:
        activity.description = data.description
    for field in [
        "registration_starts_at", "registration_deadline",
        "student_choice_starts_at", "student_choice_deadline",
        "expert_selection_starts_at", "expert_response_deadline",
        "supplement_choice_starts_at", "supplement_choice_deadline",
    ]:
        val = getattr(data, field)
        if val is not None:
            setattr(activity, field, val)
    if data.max_choices_per_student is not None:
        activity.max_choices_per_student = data.max_choices_per_student
    if data.capacity_max is not None:
        activity.capacity_max = data.capacity_max

    activity.version += 1

    from app.models.notification import AuditLog
    db.add(AuditLog(
        activity_id=activity.id,
        actor_user_id=actor.user_id,
        action="ACTIVITY_UPDATED",
        target_type="activity",
        target_id=activity.id,
        detail={"reason": data.reason, "fields_changed": data.model_dump(exclude_unset=True, exclude={"reason", "expected_version"})},
    ))
    return _to_view(activity)


async def publish_activity(
    db: AsyncSession, actor: CurrentActor, activity_id: str, expected_version: int
) -> ActivityView:
    if not await check_activity_operator(db, actor, activity_id):
        raise HTTPException(status_code=403, detail="Operator access required")

    result = await db.execute(select(Activity).where(Activity.id == activity_id))
    activity = result.scalar_one_or_none()
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    if activity.status != "DRAFT":
        raise HTTPException(status_code=409, detail="Only draft activities can be published")
    if activity.version != expected_version:
        raise HTTPException(status_code=409, detail="Version conflict")

    errors = _validate_time_order(activity)
    if errors:
        raise HTTPException(status_code=422, detail=errors)

    activity.status = "PUBLISHED"
    activity.version += 1

    from app.models.notification import AuditLog
    db.add(AuditLog(
        activity_id=activity.id,
        actor_user_id=actor.user_id,
        action="ACTIVITY_PUBLISHED",
        target_type="activity",
        target_id=activity.id,
    ))
    return _to_view(activity)
