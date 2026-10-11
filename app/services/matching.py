from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.member import ActivityMember
from app.models.registration import RegistrationSnapshot
from app.models.activity import Activity
from app.models.expert import ExpertParticipation
from app.schemas.matching import (
    MatchingInputResponse, ActivityRules, MemberView,
    EligibleExpert, StudentNeed, ExpertSections, StudentSections,
)
from app.schemas.identity import CurrentActor
from app.services.auth import check_activity_operator
from fastapi import HTTPException


async def get_matching_input(
    db: AsyncSession, actor: CurrentActor, activity_id: str
) -> MatchingInputResponse:
    if not await check_activity_operator(db, actor, activity_id):
        raise HTTPException(status_code=403, detail="Operator access required")

    activity_result = await db.execute(select(Activity).where(Activity.id == activity_id))
    activity = activity_result.scalar_one_or_none()
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    if activity.status == "DRAFT":
        raise HTTPException(status_code=409, detail="Cannot read matching input for draft activity")

    eligible_members = await db.execute(
        select(ActivityMember).where(
            ActivityMember.activity_id == activity_id,
            ActivityMember.submission_status == "SUBMITTED",
            ActivityMember.review_status == "APPROVED",
            ActivityMember.participation_status == "ACTIVE",
            ActivityMember.approved_snapshot_id.isnot(None),
        )
    )
    members = eligible_members.scalars().all()

    member_views = []
    expert_views = []
    student_views = []

    for member in members:
        member_views.append(MemberView(
            activity_id=activity_id,
            activity_member_id=member.id,
            role=member.role,
            review_status="APPROVED",
            display_name=member.public_display_name,
        ))

        snap_result = await db.execute(
            select(RegistrationSnapshot).where(RegistrationSnapshot.id == member.approved_snapshot_id)
        )
        snapshot = snap_result.scalar_one_or_none()
        if not snapshot:
            continue

        dossier = snapshot.public_dossier or {}
        content = snapshot.content or {}
        sections = content.get("sections", {})
        structured = content.get("structured", {})

        if member.role == "EXPERT":
            expert_sections = ExpertSections(
                experience=sections.get("experience", ""),
                supported_problems=sections.get("supported_problems", ""),
                boundaries=sections.get("boundaries", ""),
            )
            expert_views.append(EligibleExpert(
                activity_id=activity_id,
                activity_member_id=member.id,
                expertise=dossier.get("expertise", []),
                available=True,
                profile_summary=dossier.get("summary", structured.get("summary", "")),
                subtitle=dossier.get("subtitle", structured.get("subtitle", "")),
                sections=expert_sections,
            ))
        elif member.role == "STUDENT":
            student_sections = StudentSections(
                background=sections.get("background", ""),
                problem=sections.get("problem", ""),
                expected_help=sections.get("expected_help", ""),
            )
            student_views.append(StudentNeed(
                activity_id=activity_id,
                activity_member_id=member.id,
                title=dossier.get("title", structured.get("title", "")),
                summary=dossier.get("summary", structured.get("summary", "")),
                preferred_topics=dossier.get("topic_codes", structured.get("topic_codes", [])),
                sections=student_sections,
            ))

    activity_rules = ActivityRules(
        activity_id=activity.id,
        name=activity.name,
        status=activity.status,
        student_choice_starts_at=activity.student_choice_starts_at,
        student_choice_deadline=activity.student_choice_deadline,
        expert_selection_starts_at=activity.expert_selection_starts_at,
        expert_response_deadline=activity.expert_response_deadline,
        supplement_choice_starts_at=activity.supplement_choice_starts_at,
        supplement_choice_deadline=activity.supplement_choice_deadline,
        max_choices_per_student=activity.max_choices_per_student,
        capacity_max=activity.capacity_max,
    )

    return MatchingInputResponse(
        activity=activity_rules,
        members=member_views,
        eligible_experts=expert_views,
        student_needs=student_views,
    )
