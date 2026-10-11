from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.member import ActivityMember, MemberContact
from app.models.registration import RegistrationDraft, RegistrationSnapshot
from app.models.review import ReviewDecision
from app.models.activity import Activity
from app.models.expert import ExpertProfile, ExpertParticipation
from app.schemas.registration import DraftPatch, RegistrationView, SnapshotView
from app.schemas.identity import CurrentActor
from app.dependencies import now_iso
from fastapi import HTTPException
import re


def _check_privacy(content: dict) -> list[str]:
    warnings = []
    basic = content.get("basic", {}) or {}
    phone = basic.get("phone", "")
    if phone and re.search(r"\d{7,}", str(phone)):
        pass
    sections = content.get("sections", {}) or {}
    for key, val in sections.items():
        if val and re.search(r"1[3-9]\d{9}", str(val)):
            warnings.append(f"sections.{key} may contain phone number")
        if val and re.search(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", str(val)):
            warnings.append(f"sections.{key} may contain email")
    return warnings


def _build_public_dossier(draft: RegistrationDraft, display_name: str) -> dict:
    basic = draft.basic or {}
    sections = draft.sections or {}
    structured = draft.structured or {}

    if draft.role == "STUDENT":
        return {
            "display_name": display_name,
            "title": structured.get("title", ""),
            "summary": structured.get("summary", ""),
            "sections": {
                "background": sections.get("background", ""),
                "problem": sections.get("problem", ""),
                "expected_help": sections.get("expected_help", ""),
            },
            "industry_codes": structured.get("industry_codes", []),
            "topic_codes": structured.get("topic_codes", []),
            "service_tags": structured.get("service_tags", []),
        }
    else:
        return {
            "display_name": display_name,
            "title": structured.get("title", ""),
            "summary": structured.get("summary", ""),
            "subtitle": structured.get("subtitle", ""),
            "sections": {
                "experience": sections.get("experience", ""),
                "supported_problems": sections.get("supported_problems", ""),
                "boundaries": sections.get("boundaries", ""),
            },
            "expertise": structured.get("industry_codes", []) + structured.get("topic_codes", []),
            "industry_codes": structured.get("industry_codes", []),
            "topic_codes": structured.get("topic_codes", []),
            "service_tags": structured.get("service_tags", []),
        }


async def get_registration(
    db: AsyncSession, actor: CurrentActor, activity_id: str
) -> RegistrationView:
    result = await db.execute(
        select(ActivityMember).where(
            ActivityMember.activity_id == activity_id,
            ActivityMember.user_id == actor.user_id,
            ActivityMember.role.in_(["STUDENT", "EXPERT"]),
        )
    )
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=404, detail="No registration found")

    activity_result = await db.execute(select(Activity).where(Activity.id == activity_id))
    activity = activity_result.scalar_one()

    draft_result = await db.execute(
        select(RegistrationDraft).where(RegistrationDraft.activity_member_id == member.id)
    )
    draft = draft_result.scalar_one_or_none()

    snapshot = None
    review = None
    if member.current_submission_id:
        snap_result = await db.execute(
            select(RegistrationSnapshot).where(RegistrationSnapshot.id == member.current_submission_id)
        )
        snap = snap_result.scalar_one_or_none()
        if snap:
            snapshot = SnapshotView(
                snapshot_id=snap.id,
                activity_id=snap.activity_id,
                submitted_at=snap.submitted_at,
                submission_source=snap.submission_source,
                content=snap.content,
                public_dossier=snap.public_dossier,
            )

    if member.approved_snapshot_id:
        review_result = await db.execute(
            select(ReviewDecision).where(ReviewDecision.activity_member_id == member.id)
            .order_by(ReviewDecision.created_at.desc())
        )
        rev = review_result.scalars().first()
        if rev:
            review = {"decision": rev.decision, "reason": rev.reason, "decided_at": rev.decided_at}

    draft_dict = None
    public_preview = None
    privacy_warnings = []
    if draft:
        draft_dict = {
            "basic": draft.basic,
            "sections": draft.sections,
            "structured": draft.structured,
        }
        public_preview = _build_public_dossier(draft, member.public_display_name)
        privacy_warnings = _check_privacy({
            "basic": draft.basic,
            "sections": draft.sections,
        })

    return RegistrationView(
        activity_id=activity_id,
        activity_member_id=member.id,
        role=member.role,
        submission_status=member.submission_status,
        review_status=member.review_status,
        participation_status=member.participation_status,
        capacity_max=activity.capacity_max,
        server_time=now_iso(),
        draft=draft_dict,
        current_snapshot=snapshot,
        review_decision=review,
        public_preview=public_preview,
        privacy_warnings=privacy_warnings,
    )


async def patch_draft(
    db: AsyncSession, actor: CurrentActor, activity_id: str, data: DraftPatch
) -> RegistrationView:
    result = await db.execute(
        select(ActivityMember).where(
            ActivityMember.activity_id == activity_id,
            ActivityMember.user_id == actor.user_id,
            ActivityMember.role.in_(["STUDENT", "EXPERT"]),
        )
    )
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=404, detail="No registration found")
    if member.submission_status == "SUBMITTED":
        raise HTTPException(status_code=409, detail="Cannot edit after submission")
    if member.participation_status != "ACTIVE":
        raise HTTPException(status_code=409, detail="Member is not active")

    activity_result = await db.execute(select(Activity).where(Activity.id == activity_id))
    activity = activity_result.scalar_one()
    if activity.registration_deadline and now_iso() > activity.registration_deadline:
        raise HTTPException(status_code=409, detail="Registration window is closed")

    draft_result = await db.execute(
        select(RegistrationDraft).where(RegistrationDraft.activity_member_id == member.id)
    )
    draft = draft_result.scalar_one_or_none()
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")

    if data.basic is not None:
        existing = draft.basic or {}
        existing.update(data.basic.model_dump(exclude_unset=True))
        draft.basic = existing
    if data.sections is not None:
        existing = draft.sections or {}
        existing.update(data.sections)
        draft.sections = existing
    if data.structured is not None:
        existing = draft.structured or {}
        existing.update(data.structured)
        draft.structured = data.structured

    member.version += 1

    from app.models.notification import AuditLog
    db.add(AuditLog(
        activity_id=activity_id,
        actor_user_id=actor.user_id,
        action="DRAFT_UPDATED",
        target_type="activity_member",
        target_id=member.id,
    ))
    return await get_registration(db, actor, activity_id)


async def submit_registration(
    db: AsyncSession, actor: CurrentActor, activity_id: str, confirmed: bool
) -> RegistrationView:
    if not confirmed:
        raise HTTPException(status_code=422, detail="Must confirm submission")

    result = await db.execute(
        select(ActivityMember).where(
            ActivityMember.activity_id == activity_id,
            ActivityMember.user_id == actor.user_id,
            ActivityMember.role.in_(["STUDENT", "EXPERT"]),
        )
    )
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=404, detail="No registration found")
    if member.submission_status == "SUBMITTED":
        raise HTTPException(status_code=409, detail="Already submitted")

    activity_result = await db.execute(select(Activity).where(Activity.id == activity_id))
    activity = activity_result.scalar_one()
    if activity.registration_deadline and now_iso() > activity.registration_deadline:
        raise HTTPException(status_code=409, detail="Registration window is closed")

    draft_result = await db.execute(
        select(RegistrationDraft).where(RegistrationDraft.activity_member_id == member.id)
    )
    draft = draft_result.scalar_one_or_none()
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")

    basic = draft.basic or {}
    required = ["name", "phone", "branch"]
    for field in required:
        if not basic.get(field):
            raise HTTPException(status_code=422, detail=f"Missing required field: basic.{field}")
    if basic.get("branch") == "OTHER" and not basic.get("branch_other"):
        raise HTTPException(status_code=422, detail="OTHER branch requires explanation")

    sections = draft.sections or {}
    if member.role == "STUDENT":
        for key in ["background", "problem", "expected_help"]:
            if not sections.get(key):
                raise HTTPException(status_code=422, detail=f"Missing required section: {key}")
    else:
        for key in ["experience", "supported_problems", "boundaries"]:
            if not sections.get(key):
                raise HTTPException(status_code=422, detail=f"Missing required section: {key}")

    public_dossier = _build_public_dossier(draft, member.public_display_name)
    content = {
        "basic": draft.basic,
        "sections": draft.sections,
        "structured": draft.structured,
    }

    snapshot = RegistrationSnapshot(
        activity_id=activity_id,
        activity_member_id=member.id,
        content=content,
        public_dossier=public_dossier,
        submitted_by_user_id=actor.user_id,
        submission_source="SELF",
        submitted_at=now_iso(),
    )
    db.add(snapshot)
    await db.flush()

    member.current_submission_id = snapshot.id
    member.submission_status = "SUBMITTED"
    member.review_status = "PENDING"
    member.version += 1

    contact_result = await db.execute(
        select(MemberContact).where(MemberContact.activity_member_id == member.id)
    )
    if not contact_result.scalar_one_or_none():
        contact = MemberContact(
            activity_member_id=member.id,
            name=basic["name"],
            phone=basic["phone"],
            wechat=basic.get("wechat"),
            version=1,
        )
        db.add(contact)

    if member.role == "EXPERT":
        profile_result = await db.execute(
            select(ExpertProfile).where(ExpertProfile.user_id == actor.user_id)
        )
        profile = profile_result.scalar_one_or_none()
        if not profile:
            profile = ExpertProfile(user_id=actor.user_id)
            db.add(profile)
            await db.flush()

        part_result = await db.execute(
            select(ExpertParticipation).where(ExpertParticipation.activity_member_id == member.id)
        )
        if not part_result.scalar_one_or_none():
            db.add(ExpertParticipation(activity_member_id=member.id))

    from app.models.notification import AuditLog, OutboxEvent
    db.add(AuditLog(
        activity_id=activity_id,
        actor_user_id=actor.user_id,
        action="REGISTRATION_SUBMITTED",
        target_type="activity_member",
        target_id=member.id,
        detail={"snapshot_id": snapshot.id},
    ))
    db.add(OutboxEvent(
        event_type="REGISTRATION_SUBMITTED",
        activity_id=activity_id,
        payload={"activity_member_id": member.id, "role": member.role},
    ))
    return await get_registration(db, actor, activity_id)


async def withdraw_registration(
    db: AsyncSession, actor: CurrentActor, activity_id: str, reason: str
) -> RegistrationView:
    result = await db.execute(
        select(ActivityMember).where(
            ActivityMember.activity_id == activity_id,
            ActivityMember.user_id == actor.user_id,
            ActivityMember.role.in_(["STUDENT", "EXPERT"]),
        )
    )
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=404, detail="No registration found")
    if member.participation_status != "ACTIVE":
        raise HTTPException(status_code=409, detail="Member is not active")

    member.participation_status = "WITHDRAWN"
    member.version += 1

    from app.models.notification import AuditLog, OutboxEvent
    db.add(AuditLog(
        activity_id=activity_id,
        actor_user_id=actor.user_id,
        action="MEMBER_WITHDRAWN",
        target_type="activity_member",
        target_id=member.id,
        detail={"reason": reason},
    ))
    db.add(OutboxEvent(
        event_type="PARTICIPATION_CHANGED",
        activity_id=activity_id,
        payload={"activity_member_id": member.id, "status": "WITHDRAWN"},
    ))
    return await get_registration(db, actor, activity_id)
