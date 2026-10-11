from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.dependencies import require_operator
from app.schemas.identity import CurrentActor
from app.schemas.matching import MatchingInputResponse
from app.services.matching import get_matching_input

router = APIRouter(prefix="/api/v1/internal/activities", tags=["matching"])


@router.get("/{activity_id}/matching-input", response_model=MatchingInputResponse)
async def matching_input(
    activity_id: str,
    actor: CurrentActor = Depends(require_operator),
    db: AsyncSession = Depends(get_db),
):
    return await get_matching_input(db, actor, activity_id)
