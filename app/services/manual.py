from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.member import ActivityMember, MemberContact
from app.models.registration import RegistrationDraft, RegistrationSnapshot
from app.models.review import ReviewDecision
from app.models.activity import Activity
from app.models.expert import ExpertProfile, ExpertParticipation
from app.models.notification import AuditLog, OutboxEvent
from app.schemas.identity import CurrentActor
from app.schemas.manual import ManualExpertInput, ManualDraftPatch, ManualSubmitInput
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


async def create_manual_expert(
    db: AsyncSession, actor: CurrentActor, activity_id: str, data: ManualExpertInput
) -> ActivityMember:
    activity_result = await db.execute(select(Activity).where(Activity.id == activity_id))
    activity = activity_result.scalar_one_or_none()
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")

    existing_result = await db.execute(
        select(ActivityMember).where(
            ActivityMember.activity_id == activity_id,
            ActivityMember.user_id == data.user_id if data.user_id else ActivityMember.user_id.isnot(None),
            ActivityMember.role == "EXPERT",
        )
    )
    if existing_result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Expert already exists in this activity")

    from app.models.user import User
    if data.user_id:
        user_result = await db.execute(select(User).where(User.id == data.user_id))
        user = user_result.scalar_one_or_none()
        if not user:
            user = User(id=data.user_id, name=data.name, stable_number=f"EXP-{data.name[:4]}")
            db.add(user)
            await db.flush()
        user_id = data.user_id
    else:
        from app.database import generate_uuid
        user_id = generate_uuid()
        user = User(id=user_id, name=data.name, is_placeholder=True)
        db.add(user)
        await db.flush()

    member = ActivityMember(
        activity_id=activity_id,
        user_id=user_id,
        role="EXPERT",
        submission_status="DRAFT",
        review_status="NOT_STARTED",
        participation_status="ACTIVE",
        public_display_name=data.name,
        version=1,
    )
    db.add(member)
    await db.flush()

    contact = MemberContact(
        activity_member_id=member.id,
        name=data.name,
        phone=data.phone,
        wechat=data.wechat,
        version=1,
    )
    db.add(contact)

    draft = RegistrationDraft(
        activity_member_id=member.id,
        role="EXPERT",
        basic={
            "name": data.name,
            "phone": data.phone,
            "wechat": data.wechat,
            "branch": data.branch,
            "branch_other": data.branch_other,
            "identity": data.identity,
            "project": data.project,
            "industries": data.industries,
        },
        sections={},
        structured={
            "industry_codes": data.industries or [],
            "topic_codes": data.topics or [],
        },
    )
    db.add(draft)

    db.add(ExpertParticipation(activity_member_id=member.id))

    db.add(AuditLog(
        activity_id=activity_id,
        actor_user_id=actor.user_id,
        action="MANUAL_EXPERT_CREATED",
        target_type="activity_member",
        target_id=member.id,
        detail={"user_id": user_id, "name": data.name},
    ))

    return member


async def patch_manual_draft(
    db: AsyncSession, actor: CurrentActor, activity_id: str, member_id: str, data: ManualDraftPatch
) -> dict:
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

    draft_result = await db.execute(
        select(RegistrationDraft).where(RegistrationDraft.activity_member_id == member_id)
    )
    draft = draft_result.scalar_one_or_none()
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")

    if data.basic is not None:
        existing = draft.basic or {}
        existing.update(data.basic)
        draft.basic = existing
    if data.sections is not None:
        existing = draft.sections or {}
        existing.update(data.sections)
        draft.sections = existing
    if data.structured is not None:
        draft.structured = data.structured

    member.version += 1

    db.add(AuditLog(
        activity_id=activity_id,
        actor_user_id=actor.user_id,
        action="MANUAL_DRAFT_UPDATED",
        target_type="activity_member",
        target_id=member_id,
    ))

    return {
        "activity_member_id": member.id,
        "submission_status": member.submission_status,
        "version": member.version,
    }


async def submit_manual_expert(
    db: AsyncSession, actor: CurrentActor, activity_id: str, member_id: str, data: ManualSubmitInput
) -> dict:
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

    draft_result = await db.execute(
        select(RegistrationDraft).where(RegistrationDraft.activity_member_id == member_id)
    )
    draft = draft_result.scalar_one_or_none()
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")

    basic = draft.basic or {}
    required = ["name", "phone", "branch"]
    for field in required:
        if not basic.get(field):
            raise HTTPException(status_code=422, detail=f"Missing required field: basic.{field}")

    sections = draft.sections or {}
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
        activity_member_id=member_id,
        content=content,
        public_dossier=public_dossier,
        submitted_by_user_id=actor.user_id,
        submission_source="OPERATOR_MANUAL",
        submitted_at=now_iso(),
    )
    db.add(snapshot)
    await db.flush()

    member.current_submission_id = snapshot.id
    member.submission_status = "SUBMITTED"
    member.review_status = "PENDING"
    member.version += 1

    profile_result = await db.execute(
        select(ExpertProfile).where(ExpertProfile.user_id == member.user_id)
    )
    profile = profile_result.scalar_one_or_none()
    if not profile:
        profile = ExpertProfile(user_id=member.user_id)
        db.add(profile)
        await db.flush()

    part_result = await db.execute(
        select(ExpertParticipation).where(ExpertParticipation.activity_member_id == member_id)
    )
    if not part_result.scalar_one_or_none():
        db.add(ExpertParticipation(activity_member_id=member_id))

    db.add(AuditLog(
        activity_id=activity_id,
        actor_user_id=actor.user_id,
        action="MANUAL_EXPERT_SUBMITTED",
        target_type="activity_member",
        target_id=member_id,
        detail={"snapshot_id": snapshot.id, "confirmation_basis": data.confirmation_basis},
    ))
    db.add(OutboxEvent(
        event_type="REGISTRATION_SUBMITTED",
        activity_id=activity_id,
        payload={"activity_member_id": member_id, "role": "EXPERT", "source": "OPERATOR_MANUAL"},
    ))

    return {
        "activity_member_id": member.id,
        "submission_status": member.submission_status,
        "review_status": member.review_status,
        "version": member.version,
    }
