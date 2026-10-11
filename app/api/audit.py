from fastapi import APIRouter, Depends, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.dependencies import require_operator, pagination
from app.schemas.identity import CurrentActor
from app.schemas.audit import AuditView, DashboardView
from app.schemas.common import Page
from app.services.audit import get_dashboard, list_audit_logs, export_csv
import io

router = APIRouter(prefix="/api/v1/activities/{activity_id}", tags=["audit"])


@router.get("/registration-dashboard", response_model=DashboardView)
async def dashboard(
    activity_id: str,
    actor: CurrentActor = Depends(require_operator),
    db: AsyncSession = Depends(get_db),
):
    return await get_dashboard(db, actor, activity_id)


@router.get("/audit-logs", response_model=Page[AuditView])
async def logs(
    activity_id: str,
    page: int = 1, page_size: int = 20,
    action: str | None = None,
    actor: CurrentActor = Depends(require_operator),
    db: AsyncSession = Depends(get_db),
):
    return await list_audit_logs(db, actor, activity_id, page, page_size, action=action)


@router.get("/registration-export")
async def export(
    activity_id: str,
    role: str | None = None,
    review_status: str | None = None,
    actor: CurrentActor = Depends(require_operator),
    db: AsyncSession = Depends(get_db),
):
    csv_content = await export_csv(db, actor, activity_id, role=role, review_status=review_status)
    bom = "\ufeff"
    output = io.StringIO(bom + csv_content)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f"attachment; filename=registration-{activity_id}.csv",
            "Cache-Control": "no-store",
        },
    )
