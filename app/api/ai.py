from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.dependencies import get_current_actor, pagination
from app.schemas.identity import CurrentActor
from app.schemas.ai import (
    AiSessionInput, MessageInput, MessageAccepted,
    DossierJobInput, JobView, AiSessionView, AiMessageView,
)
from app.schemas.common import Page
from app.services.ai_service import (
    create_session, list_messages, send_message,
    create_dossier_job, get_job, retry_job,
)

router = APIRouter(prefix="/api/v1/activities/{activity_id}", tags=["ai"])


@router.post("/me/ai-sessions", response_model=AiSessionView)
async def create_ai_session(
    activity_id: str,
    data: AiSessionInput,
    actor: CurrentActor = Depends(get_current_actor),
    db: AsyncSession = Depends(get_db),
):
    return await create_session(db, actor, activity_id, data)


@router.get("/me/ai-sessions/{session_id}/messages", response_model=Page[AiMessageView])
async def get_messages(
    activity_id: str,
    session_id: str,
    page: int = 1, page_size: int = 50,
    actor: CurrentActor = Depends(get_current_actor),
    db: AsyncSession = Depends(get_db),
):
    return await list_messages(db, actor, activity_id, session_id, page, page_size)


@router.post("/me/ai-sessions/{session_id}/messages", response_model=MessageAccepted, status_code=202)
async def send_msg(
    activity_id: str,
    session_id: str,
    data: MessageInput,
    actor: CurrentActor = Depends(get_current_actor),
    db: AsyncSession = Depends(get_db),
):
    return await send_message(db, actor, activity_id, session_id, data)


@router.post("/me/dossier-jobs", response_model=JobView, status_code=202)
async def create_dossier(
    activity_id: str,
    data: DossierJobInput,
    actor: CurrentActor = Depends(get_current_actor),
    db: AsyncSession = Depends(get_db),
):
    return await create_dossier_job(db, actor, activity_id, data)


@router.get("/jobs/{job_id}", response_model=JobView)
async def get_job_status(
    job_id: str,
    actor: CurrentActor = Depends(get_current_actor),
    db: AsyncSession = Depends(get_db),
):
    return await get_job(db, actor, job_id)


@router.post("/jobs/{job_id}/retries", response_model=JobView, status_code=202)
async def retry(
    job_id: str,
    actor: CurrentActor = Depends(get_current_actor),
    db: AsyncSession = Depends(get_db),
):
    return await retry_job(db, actor, job_id)
