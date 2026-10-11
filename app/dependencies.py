from fastapi import Depends, Header, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.dev_session import DevSession
from app.models.role_grant import RoleGrant
from app.models.user import User
from app.schemas.identity import CurrentActor
from datetime import datetime, timezone
import hashlib


async def get_current_actor(
    authorization: str | None = Header(None),
    db: AsyncSession = Depends(get_db),
) -> CurrentActor:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization")
    token = authorization.removeprefix("Bearer ").strip()
    token_hash = hashlib.sha256(token.encode()).hexdigest()

    result = await db.execute(
        select(DevSession).where(DevSession.token_hash == token_hash)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")

    expires = datetime.fromisoformat(session.expires_at)
    if expires < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="Session expired")

    user_result = await db.execute(select(User).where(User.id == session.user_id))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    is_operator = False
    if session.activity_id:
        grant_result = await db.execute(
            select(RoleGrant).where(
                RoleGrant.user_id == session.user_id,
                RoleGrant.activity_id == session.activity_id,
                RoleGrant.role == "OPERATOR",
            )
        )
        is_operator = grant_result.scalar_one_or_none() is not None

        global_result = await db.execute(
            select(RoleGrant).where(
                RoleGrant.user_id == session.user_id,
                RoleGrant.activity_id.is_(None),
                RoleGrant.role == "OPERATOR",
                RoleGrant.scope == "GLOBAL",
            )
        )
        if global_result.scalar_one_or_none():
            is_operator = True

    return CurrentActor(
        user_id=session.user_id,
        name=user.name,
        activity_id=session.activity_id,
        role=session.role,
        is_operator=is_operator,
    )


def require_operator(actor: CurrentActor = Depends(get_current_actor)) -> CurrentActor:
    if not actor.is_operator:
        raise HTTPException(status_code=403, detail="Operator access required")
    return actor


def pagination(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> tuple[int, int]:
    return page, page_size


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
