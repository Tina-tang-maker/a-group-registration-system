from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.dependencies import require_operator, pagination
from app.schemas.identity import CurrentActor
from app.schemas.coverage import CoverageJobInput, CoverageAlertView, CoverageReviewInput
from app.schemas.common import Page
from app.services.coverage import run_coverage_analysis, list_coverage_alerts, add_coverage_review

router = APIRouter(prefix="/api/v1/activities/{activity_id}", tags=["coverage"])


@router.post("/coverage-jobs", status_code=202)
async def create_coverage_job(
    activity_id: str,
    actor: CurrentActor = Depends(require_operator),
    db: AsyncSession = Depends(get_db),
):
    return await run_coverage_analysis(db, actor, activity_id)


@router.get("/coverage-alerts", response_model=Page[CoverageAlertView])
async def get_alerts(
    activity_id: str,
    page: int = 1, page_size: int = 20,
    status: str | None = None,
    category: str | None = None,
    actor: CurrentActor = Depends(require_operator),
    db: AsyncSession = Depends(get_db),
):
    return await list_coverage_alerts(db, actor, activity_id, page, page_size, status=status, category=category)


@router.post("/coverage-alerts/{alert_id}/reviews", response_model=CoverageAlertView)
async def add_review(
    activity_id: str,
    alert_id: str,
    data: CoverageReviewInput,
    actor: CurrentActor = Depends(require_operator),
    db: AsyncSession = Depends(get_db),
):
    return await add_coverage_review(db, actor, activity_id, alert_id, data)
