from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.member import ActivityMember
from app.models.ai import AiSession, AiMessage, AiJob
from app.models.activity import Activity
from app.schemas.ai import (
    AiSessionInput, MessageInput, MessageAccepted,
    DossierJobInput, JobView, AiSessionView, AiMessageView,
)
from app.schemas.common import Page
from app.schemas.identity import CurrentActor
from app.dependencies import now_iso
from fastapi import HTTPException
from app.database import generate_uuid


async def create_session(
    db: AsyncSession, actor: CurrentActor, activity_id: str, data: AiSessionInput
) -> AiSessionView:
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
        raise HTTPException(status_code=409, detail="Cannot create session after submission")
    if member.participation_status != "ACTIVE":
        raise HTTPException(status_code=409, detail="Member is not active")

    activity_result = await db.execute(select(Activity).where(Activity.id == activity_id))
    activity = activity_result.scalar_one()
    if activity.registration_deadline and now_iso() > activity.registration_deadline:
        raise HTTPException(status_code=409, detail="Registration window is closed")

    existing = await db.execute(
        select(AiSession).where(
            AiSession.activity_member_id == member.id,
            AiSession.topic_key == data.topic_key,
            AiSession.status == "ACTIVE",
        )
    )
    session = existing.scalar_one_or_none()
    if session:
        return AiSessionView(
            id=session.id,
            activity_member_id=session.activity_member_id,
            topic_key=session.topic_key,
            status=session.status,
        )

    session = AiSession(
        activity_member_id=member.id,
        topic_key=data.topic_key,
        status="ACTIVE",
    )
    db.add(session)
    await db.flush()

    return AiSessionView(
        id=session.id,
        activity_member_id=session.activity_member_id,
        topic_key=session.topic_key,
        status=session.status,
    )


async def list_messages(
    db: AsyncSession, actor: CurrentActor, activity_id: str,
    session_id: str, page: int, page_size: int
) -> Page[AiMessageView]:
    result = await db.execute(
        select(ActivityMember).where(
            ActivityMember.activity_id == activity_id,
            ActivityMember.user_id == actor.user_id,
        )
    )
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=403, detail="Access denied")

    session_result = await db.execute(
        select(AiSession).where(
            AiSession.id == session_id,
            AiSession.activity_member_id == member.id,
        )
    )
    if not session_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Session not found")

    from sqlalchemy import func
    query = select(AiMessage).where(AiMessage.session_id == session_id)
    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    items_q = query.order_by(AiMessage.created_at.asc()).offset((page - 1) * page_size).limit(page_size)
    msg_result = await db.execute(items_q)
    messages = msg_result.scalars().all()

    items = [
        AiMessageView(
            id=m.id,
            session_id=m.session_id,
            role=m.role,
            content=m.content,
            created_at=m.created_at.isoformat(),
        )
        for m in messages
    ]
    return Page(items=items, total=total, page=page, page_size=page_size)


async def send_message(
    db: AsyncSession, actor: CurrentActor, activity_id: str,
    session_id: str, data: MessageInput
) -> MessageAccepted:
    result = await db.execute(
        select(ActivityMember).where(
            ActivityMember.activity_id == activity_id,
            ActivityMember.user_id == actor.user_id,
        )
    )
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=403, detail="Access denied")

    session_result = await db.execute(
        select(AiSession).where(
            AiSession.id == session_id,
            AiSession.activity_member_id == member.id,
        )
    )
    session = session_result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    existing = await db.execute(
        select(AiMessage).where(
            AiMessage.session_id == session_id,
            AiMessage.client_message_id == data.client_message_id,
        )
    )
    dup = existing.scalar_one_or_none()
    if dup:
        return MessageAccepted(message_id=dup.id, job_id=None, status="DUPLICATE")

    message = AiMessage(
        session_id=session_id,
        role="USER",
        content=data.content,
        client_message_id=data.client_message_id,
    )
    db.add(message)
    await db.flush()

    member.version += 1

    job = AiJob(
        session_id=session_id,
        activity_member_id=member.id,
        job_type="REPLY",
        status="PENDING",
        input_data={"content": data.content, "role": member.role, "topic_key": session.topic_key},
        input_version=member.version,
        input_message_ids=[message.id],
        attempts=0,
    )
    db.add(job)
    await db.flush()

    return MessageAccepted(message_id=message.id, job_id=job.id, status="ACCEPTED")


async def create_dossier_job(
    db: AsyncSession, actor: CurrentActor, activity_id: str, data: DossierJobInput
) -> JobView:
    result = await db.execute(
        select(ActivityMember).where(
            ActivityMember.activity_id == activity_id,
            ActivityMember.user_id == actor.user_id,
        )
    )
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=403, detail="Access denied")

    session_result = await db.execute(
        select(AiSession).where(
            AiSession.id == data.session_id,
            AiSession.activity_member_id == member.id,
        )
    )
    session = session_result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    msgs_result = await db.execute(
        select(AiMessage).where(AiMessage.session_id == session.id)
        .order_by(AiMessage.created_at.asc())
    )
    messages = msgs_result.scalars().all()

    from app.models.registration import RegistrationDraft
    draft_result = await db.execute(
        select(RegistrationDraft).where(RegistrationDraft.activity_member_id == member.id)
    )
    draft = draft_result.scalar_one_or_none()

    job = AiJob(
        session_id=session.id,
        activity_member_id=member.id,
        job_type="DOSSIER",
        status="PENDING",
        input_data={
            "role": member.role,
            "sections": draft.sections if draft else {},
            "structured": draft.structured if draft else {},
            "message_count": len(messages),
        },
        input_version=member.version,
        input_message_ids=[m.id for m in messages],
        attempts=0,
    )
    db.add(job)
    await db.flush()

    return JobView(
        id=job.id,
        job_type=job.job_type,
        status=job.status,
        input_version=job.input_version,
        attempts=job.attempts,
    )


async def get_job(
    db: AsyncSession, actor: CurrentActor, job_id: str
) -> JobView:
    result = await db.execute(select(AiJob).where(AiJob.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    member_result = await db.execute(
        select(ActivityMember).where(ActivityMember.id == job.activity_member_id)
    )
    member = member_result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=404, detail="Job not found")

    if member.user_id != actor.user_id and not actor.is_operator:
        raise HTTPException(status_code=403, detail="Access denied")

    return JobView(
        id=job.id,
        job_type=job.job_type,
        status=job.status,
        input_version=job.input_version,
        result_data=job.result_data,
        error_code=job.error_code,
        attempts=job.attempts,
    )


async def retry_job(
    db: AsyncSession, actor: CurrentActor, job_id: str
) -> JobView:
    result = await db.execute(select(AiJob).where(AiJob.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status != "FAILED":
        raise HTTPException(status_code=409, detail="Only failed jobs can be retried")
    if job.job_type != "REPLY":
        raise HTTPException(status_code=409, detail="Only REPLY jobs can be retried")

    member_result = await db.execute(
        select(ActivityMember).where(ActivityMember.id == job.activity_member_id)
    )
    member = member_result.scalar_one_or_none()
    if member.user_id != actor.user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    job.status = "PENDING"
    job.attempts = 0
    job.error_code = None
    job.worker_token = None
    job.lease_expires_at = None

    return JobView(
        id=job.id,
        job_type=job.job_type,
        status=job.status,
        input_version=job.input_version,
        attempts=job.attempts,
    )
