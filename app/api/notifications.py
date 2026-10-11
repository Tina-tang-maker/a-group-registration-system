from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.dependencies import get_current_actor, require_operator, pagination
from app.schemas.identity import CurrentActor
from app.schemas.notification import NotificationView, ReminderInput, ReminderResult
from app.schemas.common import Page
from app.services.notification import list_notifications, mark_read, send_reminders

router = APIRouter(prefix="/api/v1", tags=["notifications"])


@router.get("/me/notifications", response_model=Page[NotificationView])
async def get_notifications(
    page: int = 1, page_size: int = 20,
    actor: CurrentActor = Depends(get_current_actor),
    db: AsyncSession = Depends(get_db),
):
    return await list_notifications(db, actor, page, page_size)


@router.post("/me/notifications/{notification_id}/read-receipt", response_model=NotificationView)
async def read_notification(
    notification_id: str,
    actor: CurrentActor = Depends(get_current_actor),
    db: AsyncSession = Depends(get_db),
):
    return await mark_read(db, actor, notification_id)


@router.post("/activities/{activity_id}/registration-reminders", response_model=ReminderResult)
async def send_rems(
    activity_id: str,
    data: ReminderInput,
    actor: CurrentActor = Depends(require_operator),
    db: AsyncSession = Depends(get_db),
):
    return await send_reminders(db, actor, activity_id, data)
