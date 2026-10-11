"""Development seed data"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from sqlalchemy import select
from app.database import async_session_factory, engine, Base
from app.models import *
from app.config import get_settings


async def seed():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_factory() as session:
        users = [
            User(id="persona-student-1", name="张同学", stable_number="STU001"),
            User(id="persona-expert-1", name="李导师", stable_number="EXP001"),
            User(id="persona-operator-1", name="王运营", stable_number="OPS001"),
        ]
        for user in users:
            existing = await session.execute(select(User).where(User.id == user.id))
            if not existing.scalar_one_or_none():
                session.add(user)

        await session.flush()

        activity_result = await session.execute(select(Activity).where(Activity.id == "seed-activity-1"))
        activity = activity_result.scalar_one_or_none()
        if not activity:
            activity = Activity(
                id="seed-activity-1",
                name="第三期导师学员交流活动",
                description="本期活动旨在促进导师与学员之间的深度交流，帮助学员明确发展方向。",
                status="PUBLISHED",
                registration_starts_at="2026-10-01T00:00:00+08:00",
                registration_deadline="2026-10-20T23:59:59+08:00",
                student_choice_starts_at="2026-10-21T00:00:00+08:00",
                student_choice_deadline="2026-10-25T23:59:59+08:00",
                expert_selection_starts_at="2026-10-26T00:00:00+08:00",
                expert_response_deadline="2026-10-30T23:59:59+08:00",
                supplement_choice_starts_at="2026-10-31T00:00:00+08:00",
                supplement_choice_deadline="2026-11-03T23:59:59+08:00",
                max_choices_per_student=3,
                capacity_max=3,
                version=1,
            )
            session.add(activity)
            await session.flush()

        grant_result = await session.execute(
            select(RoleGrant).where(
                RoleGrant.user_id == "persona-operator-1",
                RoleGrant.activity_id == "seed-activity-1",
            )
        )
        if not grant_result.scalar_one_or_none():
            session.add(RoleGrant(
                user_id="persona-operator-1",
                activity_id="seed-activity-1",
                role="OPERATOR",
                scope="ACTIVITY",
            ))

        await session.commit()
        print("Seed data created successfully!")
        print(f"  - 3 users: 张同学(STUDENT), 李导师(EXPERT), 王运营(OPERATOR)")
        print(f"  - 1 activity: 第三期导师学员交流活动 (PUBLISHED)")
        print(f"  - 1 role grant: 王运营 -> OPERATOR")


if __name__ == "__main__":
    asyncio.run(seed())
