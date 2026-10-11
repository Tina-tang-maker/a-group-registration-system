from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.dependencies import require_operator, pagination
from app.schemas.identity import CurrentActor
from app.schemas.review import (
    ReviewInput, AdminRegistrationView, ContactPatch, ContactView,
    NoteInput, NoteView, AdminSubmitInput, ManualRegistrationInput,
    RegistrationSummary,
)
from app.schemas.common import Page
from app.services.review import (
    list_registrations, get_admin_registration, review_registration,
    patch_contact, add_note, deactivate_member, admin_withdraw,
    manual_registration, admin_patch_draft, admin_submit,
)

router = APIRouter(prefix="/api/v1/activities/{activity_id}", tags=["admin"])


@router.get("/registrations", response_model=Page[RegistrationSummary])
async def list_regs(
    activity_id: str,
    page: int = 1, page_size: int = 20,
    role: str | None = None,
    review_status: str | None = None,
    participation_status: str | None = None,
    keyword: str | None = None,
    actor: CurrentActor = Depends(require_operator),
    db: AsyncSession = Depends(get_db),
):
    return await list_registrations(
        db, actor, activity_id, page, page_size,
        role=role, review_status=review_status,
        participation_status=participation_status, keyword=keyword,
    )


@router.get("/registrations/{member_id}", response_model=AdminRegistrationView)
async def get_reg(
    activity_id: str,
    member_id: str,
    actor: CurrentActor = Depends(require_operator),
    db: AsyncSession = Depends(get_db),
):
    return await get_admin_registration(db, actor, activity_id, member_id)


@router.post("/registrations/{member_id}/reviews", response_model=AdminRegistrationView)
async def review_reg(
    activity_id: str,
    member_id: str,
    data: ReviewInput,
    actor: CurrentActor = Depends(require_operator),
    db: AsyncSession = Depends(get_db),
):
    return await review_registration(db, actor, activity_id, member_id, data)


@router.patch("/registrations/{member_id}/contact", response_model=ContactView)
async def update_contact(
    activity_id: str,
    member_id: str,
    data: ContactPatch,
    actor: CurrentActor = Depends(require_operator),
    db: AsyncSession = Depends(get_db),
):
    return await patch_contact(db, actor, activity_id, member_id, data)


@router.post("/registrations/{member_id}/notes", response_model=NoteView)
async def create_note(
    activity_id: str,
    member_id: str,
    data: NoteInput,
    actor: CurrentActor = Depends(require_operator),
    db: AsyncSession = Depends(get_db),
):
    return await add_note(db, actor, activity_id, member_id, data)


@router.post("/registrations/{member_id}/deactivation", response_model=AdminRegistrationView)
async def deactivate(
    activity_id: str,
    member_id: str,
    data: dict,
    actor: CurrentActor = Depends(require_operator),
    db: AsyncSession = Depends(get_db),
):
    return await deactivate_member(
        db, actor, activity_id, member_id,
        data.get("reason", ""), data.get("expected_version", 1),
    )


@router.post("/registrations/{member_id}/withdrawal", response_model=AdminRegistrationView)
async def admin_withdraw_reg(
    activity_id: str,
    member_id: str,
    data: dict,
    actor: CurrentActor = Depends(require_operator),
    db: AsyncSession = Depends(get_db),
):
    return await admin_withdraw(
        db, actor, activity_id, member_id,
        data.get("reason", ""), data.get("expected_version", 1),
    )


@router.patch("/registrations/{member_id}/draft", response_model=AdminRegistrationView)
async def admin_edit_draft(
    activity_id: str,
    member_id: str,
    data: dict,
    actor: CurrentActor = Depends(require_operator),
    db: AsyncSession = Depends(get_db),
):
    return await admin_patch_draft(
        db, actor, activity_id, member_id,
        data.get("draft", {}), data.get("reason", ""), data.get("expected_version", 1),
    )


@router.post("/registrations/{member_id}/submissions", response_model=AdminRegistrationView)
async def admin_submit_reg(
    activity_id: str,
    member_id: str,
    data: AdminSubmitInput,
    actor: CurrentActor = Depends(require_operator),
    db: AsyncSession = Depends(get_db),
):
    return await admin_submit(db, actor, activity_id, member_id, data)


@router.post("/manual-registrations", response_model=AdminRegistrationView, status_code=201)
async def create_manual(
    activity_id: str,
    data: ManualRegistrationInput,
    actor: CurrentActor = Depends(require_operator),
    db: AsyncSession = Depends(get_db),
):
    return await manual_registration(db, actor, activity_id, data)
