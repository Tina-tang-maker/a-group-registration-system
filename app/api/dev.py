from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.dependencies import get_current_actor, pagination
from app.schemas.identity import Persona, SelectPersona, CurrentActor
from app.schemas.common import Page
from app.services.identity import list_personas, create_dev_session, delete_dev_session, get_dictionary
from app.config import get_settings
import hashlib

router = APIRouter(prefix="/api/v1", tags=["identity"])


@router.get("/dev/personas", response_model=list[Persona])
async def get_personas(db: AsyncSession = Depends(get_db)):
    settings = get_settings()
    if not settings.is_local:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Not available")
    return await list_personas(db)


@router.post("/dev/sessions", response_model=CurrentActor)
async def create_session(
    data: SelectPersona,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    settings = get_settings()
    if not settings.is_local:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Not available")
    actor = await create_dev_session(db, data.persona_id, data.activity_id, data.role)
    response.headers["X-Dev-Token"] = actor.token
    return actor


@router.delete("/dev/sessions/current")
async def delete_session(
    actor: CurrentActor = Depends(get_current_actor),
    db: AsyncSession = Depends(get_db),
):
    from app.dependencies import get_current_actor as _
    from fastapi import Header
    return {"deleted": True}


@router.get("/me/context", response_model=CurrentActor)
async def get_context(actor: CurrentActor = Depends(get_current_actor)):
    return actor


@router.get("/dictionaries/{kind}")
async def get_dict(kind: str, actor: CurrentActor = Depends(get_current_actor)):
    return await get_dictionary(kind)
