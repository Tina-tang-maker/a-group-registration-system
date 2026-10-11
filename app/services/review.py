from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.member import ActivityMember, MemberContact
from app.models.registration import RegistrationDraft, RegistrationSnapshot
from app.models.review import ReviewDecision
from app.models.activity import Activity
from app.models.expert import ExpertProfile, ExpertParticipation
from app.models.user import User
from app.models.note import OperatorNote
from app.schemas.review import (
    ReviewInput, AdminRegistrationView, ContactPatch, NoteInput, NoteView,
    AdminSubmitInput, ManualRegistrationInput, ContactView, RegistrationSummary,
)
from app.schemas.common import Page
from app.schemas.identity import CurrentActor
from app.services.auth import check_activity_operator
from app.dependencies import now_iso
from fastapi import HTTPException


async def list_registrations(
    db: AsyncSession, actor: CurrentActor, activity_id: str,
    page: int, page_size: int,
    role: str | None = None, review_status: str | None = None,
    participation_status: str | None = None, keyword: str | None = None,
) -> Page[RegistrationSummary]:
    if not await check_activity_operator(db, actor, activity_id):
        raise HTTPException(status_code=403, detail="Operator access required")

    query = select(ActivityMember).where(ActivityMember.activity_id == activity_id)
    if role:
        query = query.where(ActivityMember.role == role)
    if review_status:
        query = query.where(ActivityMember.review_status == review_status)
    if participation_status:
        query = query.where(ActivityMember.participation_status == participation_status)

    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    items_q = query.order_by(ActivityMember.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(items_q)
    members = result.scalars().all()

    items = [
        RegistrationSummary(
            activity_member_id=m.id,
            user_id=m.user_id,
            role=m.role,
            display_name=m.public_display_name,
            submission_status=m.submission_status,
            review_status=m.review_status,
            participation_status=m.participation_status,
        )
        for m in members
    ]
    return Page(items=items, total=total, page=page, page_size=page_size)


async def get_admin_registration(
    db: AsyncSession, actor: CurrentActor, activity_id: str, member_id: str
) -> AdminRegistrationView:
    if not await check_activity_operator(db, actor, activity_id):
        raise HTTPException(status_code=403, detail="Operator access required")

    result = await db.execute(
        select(ActivityMember).where(
            ActivityMember.id == member_id,
            ActivityMember.activity_id == activity_id,
        )
    )
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    contact_view = None
    contact_result = await db.execute(
        select(MemberContact).where(MemberContact.activity_member_id == member.id)
    )
    contact = contact_result.scalar_one_or_none()
    if contact:
        contact_view = ContactView(
            activity_member_id=contact.activity_member_id,
            name=contact.name,
            phone=contact.phone,
            wechat=contact.wechat,
            version=contact.version,
        )

    draft_dict = None
    draft_result = await db.execute(
        select(RegistrationDraft).where(RegistrationDraft.activity_member_id == member.id)
    )
    draft = draft_result.scalar_one_or_none()
    if draft:
        draft_dict = {"basic": draft.basic, "sections": draft.sections, "structured": draft.structured}

    snapshot_dict = None
    if member.current_submission_id:
        snap_result = await db.execute(
            select(RegistrationSnapshot).where(RegistrationSnapshot.id == member.current_submission_id)
        )
        snap = snap_result.scalar_one_or_none()
        if snap:
            snapshot_dict = {
                "snapshot_id": snap.id,
                "content": snap.content,
                "public_dossier": snap.public_dossier,
                "submitted_at": snap.submitted_at,
                "submission_source": snap.submission_source,
            }

    reviews_result = await db.execute(
        select(ReviewDecision).where(ReviewDecision.activity_member_id == member.id)
        .order_by(ReviewDecision.created_at.desc())
    )
    reviews = [
        {"decision": r.decision, "reason": r.reason, "reviewer_id": r.reviewer_id, "decided_at": r.decided_at}
        for r in reviews_result.scalars().all()
    ]

    notes_result = await db.execute(
        select(OperatorNote).where(OperatorNote.activity_member_id == member.id)
        .order_by(OperatorNote.created_at.asc())
    )
    notes = [
        NoteView(id=n.id, content=n.content, author_id=n.author_id, created_at=n.created_at.isoformat())
        for n in notes_result.scalars().all()
    ]

    return AdminRegistrationView(
        activity_id=activity_id,
        activity_member_id=member.id,
        user_id=member.user_id,
        role=member.role,
        submission_status=member.submission_status,
        review_status=member.review_status,
        participation_status=member.participation_status,
        version=member.version,
        contact=contact_view,
        draft=draft_dict,
        current_snapshot=snapshot_dict,
        review_decisions=reviews,
        notes=notes,
    )


async def review_registration(
    db: AsyncSession, actor: CurrentActor, activity_id: str,
    member_id: str, data: ReviewInput
) -> AdminRegistrationView:
    if not await check_activity_operator(db, actor, activity_id):
        raise HTTPException(status_code=403, detail="Operator access required")

    result = await db.execute(
        select(ActivityMember).where(
            ActivityMember.id == member_id,
            ActivityMember.activity_id == activity_id,
        )
    )
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    if member.review_status != "PENDING":
        raise HTTPException(status_code=409, detail="No pending review for this member")
    if member.version != data.expected_version:
        raise HTTPException(status_code=409, detail="Version conflict")
    if not member.current_submission_id:
        raise HTTPException(status_code=409, detail="No submission to review")
    if data.decision == "REJECTED" and not data.reason:
        raise HTTPException(status_code=422, detail="Rejection requires a reason")

    review = ReviewDecision(
        snapshot_id=member.current_submission_id,
        activity_member_id=member.id,
        decision=data.decision,
        reason=data.reason,
        reviewer_id=actor.user_id,
        decided_at=now_iso(),
    )
    db.add(review)

    member.review_status = data.decision
    if data.decision == "APPROVED":
        member.approved_snapshot_id = member.current_submission_id
        if member.role == "EXPERT":
            part_result = await db.execute(
                select(ExpertParticipation).where(ExpertParticipation.activity_member_id == member.id)
            )
            part = part_result.scalar_one_or_none()
            if part:
                part.approved_snapshot_id = member.current_submission_id

            profile_result = await db.execute(
                select(ExpertProfile).where(ExpertProfile.user_id == member.user_id)
            )
            profile = profile_result.scalar_one_or_none()
            if profile:
                profile.latest_confirmed_snapshot_id = member.current_submission_id
    member.version += 1

    from app.models.notification import AuditLog, OutboxEvent, Notification
    db.add(AuditLog(
        activity_id=activity_id,
        actor_user_id=actor.user_id,
        action=f"REVIEW_{data.decision}",
        target_type="activity_member",
        target_id=member.id,
        detail={"reason": data.reason},
    ))
    db.add(OutboxEvent(
        event_type="REVIEW_DECIDED",
        activity_id=activity_id,
        payload={"activity_member_id": member.id, "decision": data.decision},
    ))
    title = "审核通过" if data.decision == "APPROVED" else "审核驳回"
    db.add(Notification(
        user_id=member.user_id,
        activity_id=activity_id,
        notification_type="REVIEW_RESULT",
        title=title,
        body=data.reason if data.decision == "REJECTED" else "您的报名资料已通过审核",
        target_id=member.id,
    ))
    return await get_admin_registration(db, actor, activity_id, member_id)


async def patch_contact(
    db: AsyncSession, actor: CurrentActor, activity_id: str,
    member_id: str, data: ContactPatch
) -> ContactView:
    if not await check_activity_operator(db, actor, activity_id):
        raise HTTPException(status_code=403, detail="Operator access required")

    result = await db.execute(
        select(ActivityMember).where(
            ActivityMember.id == member_id,
            ActivityMember.activity_id == activity_id,
        )
    )
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    contact_result = await db.execute(
        select(MemberContact).where(MemberContact.activity_member_id == member.id)
    )
    contact = contact_result.scalar_one_or_none()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    if contact.version != data.expected_version:
        raise HTTPException(status_code=409, detail="Version conflict")

    if data.name is not None:
        contact.name = data.name
    if data.phone is not None:
        contact.phone = data.phone
    if data.wechat is not None:
        contact.wechat = data.wechat
    contact.version += 1

    from app.models.notification import AuditLog
    db.add(AuditLog(
        activity_id=activity_id,
        actor_user_id=actor.user_id,
        action="CONTACT_UPDATED",
        target_type="activity_member",
        target_id=member.id,
        detail={"reason": data.reason},
    ))
    return ContactView(
        activity_member_id=contact.activity_member_id,
        name=contact.name,
        phone=contact.phone,
        wechat=contact.wechat,
        version=contact.version,
    )


async def add_note(
    db: AsyncSession, actor: CurrentActor, activity_id: str,
    member_id: str, data: NoteInput
) -> NoteView:
    if not await check_activity_operator(db, actor, activity_id):
        raise HTTPException(status_code=403, detail="Operator access required")

    result = await db.execute(
        select(ActivityMember).where(
            ActivityMember.id == member_id,
            ActivityMember.activity_id == activity_id,
        )
    )
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    note = OperatorNote(
        activity_id=activity_id,
        activity_member_id=member.id,
        author_id=actor.user_id,
        content=data.content,
    )
    db.add(note)
    await db.flush()

    from app.models.notification import AuditLog
    db.add(AuditLog(
        activity_id=activity_id,
        actor_user_id=actor.user_id,
        action="OPERATOR_NOTE_ADDED",
        target_type="activity_member",
        target_id=member.id,
    ))
    return NoteView(id=note.id, content=note.content, author_id=note.author_id, created_at=note.created_at.isoformat())


async def deactivate_member(
    db: AsyncSession, actor: CurrentActor, activity_id: str,
    member_id: str, reason: str, expected_version: int
) -> AdminRegistrationView:
    if not await check_activity_operator(db, actor, activity_id):
        raise HTTPException(status_code=403, detail="Operator access required")

    result = await db.execute(
        select(ActivityMember).where(
            ActivityMember.id == member_id,
            ActivityMember.activity_id == activity_id,
        )
    )
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    if member.version != expected_version:
        raise HTTPException(status_code=409, detail="Version conflict")
    if member.participation_status != "ACTIVE":
        raise HTTPException(status_code=409, detail="Member is not active")

    member.participation_status = "INACTIVE"
    member.version += 1

    from app.models.notification import AuditLog, OutboxEvent
    db.add(AuditLog(
        activity_id=activity_id,
        actor_user_id=actor.user_id,
        action="MEMBER_DEACTIVATED",
        target_type="activity_member",
        target_id=member.id,
        detail={"reason": reason},
    ))
    db.add(OutboxEvent(
        event_type="PARTICIPATION_CHANGED",
        activity_id=activity_id,
        payload={"activity_member_id": member.id, "status": "INACTIVE"},
    ))
    return await get_admin_registration(db, actor, activity_id, member_id)


async def admin_withdraw(
    db: AsyncSession, actor: CurrentActor, activity_id: str,
    member_id: str, reason: str, expected_version: int
) -> AdminRegistrationView:
    if not await check_activity_operator(db, actor, activity_id):
        raise HTTPException(status_code=403, detail="Operator access required")

    result = await db.execute(
        select(ActivityMember).where(
            ActivityMember.id == member_id,
            ActivityMember.activity_id == activity_id,
        )
    )
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    if member.version != expected_version:
        raise HTTPException(status_code=409, detail="Version conflict")
    if member.participation_status != "ACTIVE":
        raise HTTPException(status_code=409, detail="Member is not active")

    member.participation_status = "WITHDRAWN"
    member.version += 1

    from app.models.notification import AuditLog, OutboxEvent
    db.add(AuditLog(
        activity_id=activity_id,
        actor_user_id=actor.user_id,
        action="OPERATOR_WITHDREW_MEMBER",
        target_type="activity_member",
        target_id=member.id,
        detail={"reason": reason},
    ))
    db.add(OutboxEvent(
        event_type="PARTICIPATION_CHANGED",
        activity_id=activity_id,
        payload={"activity_member_id": member.id, "status": "WITHDRAWN"},
    ))
    return await get_admin_registration(db, actor, activity_id, member_id)


async def manual_registration(
    db: AsyncSession, actor: CurrentActor, activity_id: str, data: ManualRegistrationInput
) -> AdminRegistrationView:
    if not await check_activity_operator(db, actor, activity_id):
        raise HTTPException(status_code=403, detail="Operator access required")

    activity_result = await db.execute(select(Activity).where(Activity.id == activity_id))
    activity = activity_result.scalar_one_or_none()
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    if activity.status != "PUBLISHED":
        raise HTTPException(status_code=409, detail="Activity is not open")

    user_id = data.user_id
    if not user_id:
        from app.database import generate_uuid
        from app.services.identity import DEV_PERSONAS
        user_id = f"placeholder-{generate_uuid()[:8]}"
        user = User(
            id=user_id,
            name=data.name,
            phone=data.phone,
            wechat=data.wechat,
            stable_number=f"PL{generate_uuid()[:6].upper()}",
            is_placeholder=True,
        )
        db.add(user)
        await db.flush()

    existing = await db.execute(
        select(ActivityMember).where(
            ActivityMember.activity_id == activity_id,
            ActivityMember.user_id == user_id,
            ActivityMember.role == data.role,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="User already registered for this role")

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
        user_id=user_id,
        role=data.role,
        public_display_name=display_name,
        submission_status="DRAFT",
        review_status="NOT_SUBMITTED",
        participation_status="ACTIVE",
        version=1,
    )
    db.add(member)
    await db.flush()

    draft = RegistrationDraft(
        activity_member_id=member.id,
        role=data.role,
        basic={"name": data.name, "phone": data.phone, "wechat": data.wechat, "branch": None},
        sections={},
        structured={},
    )
    db.add(draft)

    contact = MemberContact(
        activity_member_id=member.id,
        name=data.name,
        phone=data.phone,
        wechat=data.wechat,
        version=1,
    )
    db.add(contact)

    from app.models.notification import AuditLog
    db.add(AuditLog(
        activity_id=activity_id,
        actor_user_id=actor.user_id,
        action="MANUAL_REGISTRATION_CREATED",
        target_type="activity_member",
        target_id=member.id,
        detail={"user_id": user_id, "role": data.role},
    ))
    return await get_admin_registration(db, actor, activity_id, member.id)


async def admin_patch_draft(
    db: AsyncSession, actor: CurrentActor, activity_id: str,
    member_id: str, draft_data: dict, reason: str, expected_version: int
) -> AdminRegistrationView:
    if not await check_activity_operator(db, actor, activity_id):
        raise HTTPException(status_code=403, detail="Operator access required")

    result = await db.execute(
        select(ActivityMember).where(
            ActivityMember.id == member_id,
            ActivityMember.activity_id == activity_id,
        )
    )
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    if member.submission_status == "SUBMITTED":
        raise HTTPException(status_code=409, detail="Cannot edit after submission")
    if member.version != expected_version:
        raise HTTPException(status_code=409, detail="Version conflict")

    draft_result = await db.execute(
        select(RegistrationDraft).where(RegistrationDraft.activity_member_id == member.id)
    )
    draft = draft_result.scalar_one_or_none()
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")

    if "basic" in draft_data:
        existing = draft.basic or {}
        existing.update(draft_data["basic"])
        draft.basic = existing
    if "sections" in draft_data:
        existing = draft.sections or {}
        existing.update(draft_data["sections"])
        draft.sections = existing
    if "structured" in draft_data:
        existing = draft.structured or {}
        existing.update(draft_data["structured"])
        draft.structured = existing

    member.version += 1

    from app.models.notification import AuditLog
    db.add(AuditLog(
        activity_id=activity_id,
        actor_user_id=actor.user_id,
        action="OPERATOR_DRAFT_UPDATED",
        target_type="activity_member",
        target_id=member.id,
        detail={"reason": reason},
    ))
    return await get_admin_registration(db, actor, activity_id, member_id)


async def admin_submit(
    db: AsyncSession, actor: CurrentActor, activity_id: str,
    member_id: str, data: AdminSubmitInput
) -> AdminRegistrationView:
    if not await check_activity_operator(db, actor, activity_id):
        raise HTTPException(status_code=403, detail="Operator access required")

    result = await db.execute(
        select(ActivityMember).where(
            ActivityMember.id == member_id,
            ActivityMember.activity_id == activity_id,
        )
    )
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    if member.submission_status == "SUBMITTED":
        raise HTTPException(status_code=409, detail="Already submitted")
    if member.version != data.expected_version:
        raise HTTPException(status_code=409, detail="Version conflict")

    activity_result = await db.execute(select(Activity).where(Activity.id == activity_id))
    activity = activity_result.scalar_one_or_none()
    if activity.registration_deadline and now_iso() > activity.registration_deadline:
        raise HTTPException(status_code=409, detail="Registration window is closed")

    draft_result = await db.execute(
        select(RegistrationDraft).where(RegistrationDraft.activity_member_id == member.id)
    )
    draft = draft_result.scalar_one_or_none()
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")

    basic = draft.basic or {}
    for field in ["name", "phone"]:
        if not basic.get(field):
            raise HTTPException(status_code=422, detail=f"Missing required field: basic.{field}")

    from app.services.registration import _build_public_dossier
    public_dossier = _build_public_dossier(draft, member.public_display_name)
    content = {"basic": draft.basic, "sections": draft.sections, "structured": draft.structured}

    snapshot = RegistrationSnapshot(
        activity_id=activity_id,
        activity_member_id=member.id,
        content=content,
        public_dossier=public_dossier,
        submitted_by_user_id=actor.user_id,
        submission_source="OPERATOR",
        submitted_at=now_iso(),
        confirmation_basis=data.confirmation_basis,
    )
    db.add(snapshot)
    await db.flush()

    member.current_submission_id = snapshot.id
    member.submission_status = "SUBMITTED"
    member.review_status = "PENDING"
    member.version += 1

    from app.models.notification import AuditLog
    db.add(AuditLog(
        activity_id=activity_id,
        actor_user_id=actor.user_id,
        action="OPERATOR_SUBMITTED",
        target_type="activity_member",
        target_id=member.id,
        detail={"confirmation_basis": data.confirmation_basis},
    ))
    return await get_admin_registration(db, actor, activity_id, member_id)
