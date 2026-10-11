from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User
from app.models.dev_session import DevSession
from app.models.role_grant import RoleGrant
from app.schemas.identity import Persona, CurrentActor
from app.dependencies import now_iso
from datetime import datetime, timezone, timedelta
import hashlib
import secrets


DEV_PERSONAS = [
    {"id": "persona-student-1", "name": "张同学", "stable_number": "STU001"},
    {"id": "persona-expert-1", "name": "李导师", "stable_number": "EXP001"},
    {"id": "persona-operator-1", "name": "王运营", "stable_number": "OPS001"},
]


async def list_personas(db: AsyncSession) -> list[Persona]:
    return [Persona(id=p["id"], name=p["name"], stable_number=p["stable_number"]) for p in DEV_PERSONAS]


async def create_dev_session(
    db: AsyncSession, persona_id: str, activity_id: str | None, role: str | None
) -> CurrentActor:
    persona = next((p for p in DEV_PERSONAS if p["id"] == persona_id), None)
    if not persona:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Persona not found")

    user_id = persona["id"]
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        user = User(
            id=user_id,
            name=persona["name"],
            stable_number=persona["stable_number"],
            is_placeholder=False,
        )
        db.add(user)

    is_operator = False
    if activity_id and role == "OPERATOR":
        grant_result = await db.execute(
            select(RoleGrant).where(
                RoleGrant.user_id == user_id,
                RoleGrant.activity_id == activity_id,
                RoleGrant.role == "OPERATOR",
            )
        )
        if not grant_result.scalar_one_or_none():
            from app.models.role_grant import RoleGrant as RG
            db.add(RG(user_id=user_id, activity_id=activity_id, role="OPERATOR", scope="ACTIVITY"))
        is_operator = True

    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    expires = (datetime.now(timezone.utc) + timedelta(hours=12)).isoformat()

    dev_session = DevSession(
        token_hash=token_hash,
        user_id=user_id,
        activity_id=activity_id,
        role=role,
        expires_at=expires,
    )
    db.add(dev_session)
    await db.flush()

    return CurrentActor(
        user_id=user_id,
        name=persona["name"],
        activity_id=activity_id,
        role=role,
        is_operator=is_operator,
        token=raw_token,
    )


async def delete_dev_session(db: AsyncSession, token_hash: str) -> bool:
    result = await db.execute(
        select(DevSession).where(DevSession.token_hash == token_hash)
    )
    session = result.scalar_one_or_none()
    if session:
        await db.delete(session)
        return True
    return False


DICTIONARIES = {
    "branches": [
        {"code": "BEIJING", "label": "北京分社", "active": True},
        {"code": "SHANGHAI", "label": "上海分社", "active": True},
        {"code": "SHENZHEN", "label": "深圳分社", "active": True},
        {"code": "GUANGZHOU", "label": "广州分社", "active": True},
        {"code": "OTHER", "label": "其他", "active": True},
    ],
    "industries": [
        {"code": "TECH", "label": "科技/互联网", "active": True},
        {"code": "FINANCE", "label": "金融", "active": True},
        {"code": "EDUCATION", "label": "教育", "active": True},
        {"code": "HEALTH", "label": "医疗健康", "active": True},
        {"code": "MANUFACTURING", "label": "制造业", "active": True},
        {"code": "CONSULTING", "label": "咨询", "active": True},
        {"code": "NONPROFIT", "label": "公益/非营利", "active": True},
        {"code": "OTHER", "label": "其他", "active": True},
    ],
    "topics": [
        {"code": "CAREER", "label": "职业规划", "active": True},
        {"code": "MANAGEMENT", "label": "项目管理", "active": True},
        {"code": "TECH_SKILL", "label": "技术能力", "active": True},
        {"code": "ENTREPRENEURSHIP", "label": "创业", "active": True},
        {"code": "COMMUNICATION", "label": "沟通表达", "active": True},
        {"code": "LEADERSHIP", "label": "领导力", "active": True},
    ],
}


async def get_dictionary(kind: str) -> dict:
    if kind not in DICTIONARIES:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"Dictionary '{kind}' not found")
    items = DICTIONARIES[kind]
    return {
        "kind": kind,
        "items": items,
        "version": 1,
    }
