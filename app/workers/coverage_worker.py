import asyncio
from sqlalchemy import select
from app.database import async_session_factory
from app.models.activity import Activity
from app.models.ai import AiJob
from app.dependencies import now_iso
from app.database import generate_uuid
from datetime import datetime, timezone, timedelta


async def run_coverage_scan():
    while True:
        try:
            async with async_session_factory() as session:
                now = datetime.now(timezone.utc)
                threshold = now + timedelta(hours=72)

                result = await session.execute(
                    select(Activity).where(
                        Activity.status == "PUBLISHED",
                    )
                )
                activities = result.scalars().all()

                for activity in activities:
                    if not activity.registration_deadline:
                        continue
                    try:
                        deadline = datetime.fromisoformat(activity.registration_deadline)
                    except (ValueError, TypeError):
                        continue

                    if now < threshold and deadline <= threshold:
                        existing = await session.execute(
                            select(AiJob).where(
                                AiJob.job_type == "COVERAGE",
                                AiJob.input_data.contains({"trigger": "DEADLINE_72H", "activity_id": activity.id}),
                                AiJob.status == "SUCCEEDED",
                            )
                        )
                        if existing.scalar_one_or_none():
                            continue

                        job = AiJob(
                            activity_member_id="system",
                            job_type="COVERAGE",
                            status="PENDING",
                            input_data={
                                "trigger": "DEADLINE_72H",
                                "activity_id": activity.id,
                            },
                            attempts=0,
                        )
                        session.add(job)
                        await session.commit()

        except Exception as e:
            print(f"Coverage worker error: {e}")

        await asyncio.sleep(60)
