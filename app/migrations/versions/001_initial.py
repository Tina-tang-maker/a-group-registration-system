"""initial schema

Revision ID: 001
"""
from alembic import op
import sqlalchemy as sa

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "users",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("phone", sa.String(20), nullable=True),
        sa.Column("wechat", sa.String(50), nullable=True),
        sa.Column("stable_number", sa.String(50), unique=True, nullable=True),
        sa.Column("is_placeholder", sa.Boolean(), default=False, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "activities",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(20), default="DRAFT", nullable=False),
        sa.Column("registration_starts_at", sa.String(40), nullable=True),
        sa.Column("registration_deadline", sa.String(40), nullable=True),
        sa.Column("student_choice_starts_at", sa.String(40), nullable=True),
        sa.Column("student_choice_deadline", sa.String(40), nullable=True),
        sa.Column("expert_selection_starts_at", sa.String(40), nullable=True),
        sa.Column("expert_response_deadline", sa.String(40), nullable=True),
        sa.Column("supplement_choice_starts_at", sa.String(40), nullable=True),
        sa.Column("supplement_choice_deadline", sa.String(40), nullable=True),
        sa.Column("max_choices_per_student", sa.Integer(), default=3, nullable=False),
        sa.Column("capacity_max", sa.Integer(), default=3, nullable=False),
        sa.Column("version", sa.Integer(), default=1, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "activity_members",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("activity_id", sa.String(36), sa.ForeignKey("activities.id"), nullable=False),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("public_display_name", sa.String(50), nullable=False),
        sa.Column("submission_status", sa.String(20), default="DRAFT", nullable=False),
        sa.Column("review_status", sa.String(20), default="NOT_SUBMITTED", nullable=False),
        sa.Column("participation_status", sa.String(20), default="ACTIVE", nullable=False),
        sa.Column("current_submission_id", sa.String(36), nullable=True),
        sa.Column("approved_snapshot_id", sa.String(36), nullable=True),
        sa.Column("version", sa.Integer(), default=1, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("activity_id", "user_id", "role", name="uq_activity_user_role"),
    )

    op.create_table(
        "member_contacts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("activity_member_id", sa.String(36), sa.ForeignKey("activity_members.id"), unique=True, nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("phone", sa.String(20), nullable=False),
        sa.Column("wechat", sa.String(50), nullable=True),
        sa.Column("version", sa.Integer(), default=1, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "registration_drafts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("activity_member_id", sa.String(36), sa.ForeignKey("activity_members.id"), unique=True, nullable=False),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("basic", sa.JSON(), nullable=True),
        sa.Column("sections", sa.JSON(), nullable=True),
        sa.Column("structured", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "registration_snapshots",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("activity_id", sa.String(36), sa.ForeignKey("activities.id"), nullable=False),
        sa.Column("activity_member_id", sa.String(36), sa.ForeignKey("activity_members.id"), nullable=False),
        sa.Column("content", sa.JSON(), nullable=False),
        sa.Column("public_dossier", sa.JSON(), nullable=True),
        sa.Column("submitted_by_user_id", sa.String(36), nullable=True),
        sa.Column("submission_source", sa.String(20), default="SELF", nullable=False),
        sa.Column("submitted_at", sa.String(40), nullable=False),
        sa.Column("confirmation_basis", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "review_decisions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("snapshot_id", sa.String(36), sa.ForeignKey("registration_snapshots.id"), nullable=False),
        sa.Column("activity_member_id", sa.String(36), sa.ForeignKey("activity_members.id"), nullable=False),
        sa.Column("decision", sa.String(20), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("reviewer_id", sa.String(36), nullable=False),
        sa.Column("decided_at", sa.String(40), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "expert_profiles",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), unique=True, nullable=False),
        sa.Column("latest_confirmed_snapshot_id", sa.String(36), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "expert_participations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("activity_member_id", sa.String(36), sa.ForeignKey("activity_members.id"), unique=True, nullable=False),
        sa.Column("approved_snapshot_id", sa.String(36), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "role_grants",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("activity_id", sa.String(36), sa.ForeignKey("activities.id"), nullable=True),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("scope", sa.String(20), default="ACTIVITY", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "dev_sessions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("token_hash", sa.String(128), unique=True, nullable=False),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("activity_id", sa.String(36), nullable=True),
        sa.Column("role", sa.String(20), nullable=True),
        sa.Column("expires_at", sa.String(40), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "ai_sessions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("activity_member_id", sa.String(36), sa.ForeignKey("activity_members.id"), nullable=False),
        sa.Column("topic_key", sa.String(50), nullable=False),
        sa.Column("status", sa.String(20), default="ACTIVE", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "ai_messages",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("session_id", sa.String(36), sa.ForeignKey("ai_sessions.id"), nullable=False),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("client_message_id", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "ai_jobs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("session_id", sa.String(36), sa.ForeignKey("ai_sessions.id"), nullable=True),
        sa.Column("activity_member_id", sa.String(36), nullable=False),
        sa.Column("job_type", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), default="PENDING", nullable=False),
        sa.Column("input_data", sa.JSON(), nullable=True),
        sa.Column("result_data", sa.JSON(), nullable=True),
        sa.Column("error_code", sa.String(50), nullable=True),
        sa.Column("input_version", sa.Integer(), nullable=True),
        sa.Column("input_message_ids", sa.JSON(), nullable=True),
        sa.Column("worker_token", sa.String(100), nullable=True),
        sa.Column("lease_expires_at", sa.String(40), nullable=True),
        sa.Column("available_at", sa.String(40), nullable=True),
        sa.Column("attempts", sa.Integer(), default=0, nullable=False),
        sa.Column("max_attempts", sa.Integer(), default=3, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "coverage_alerts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("activity_id", sa.String(36), sa.ForeignKey("activities.id"), nullable=False),
        sa.Column("student_member_id", sa.String(36), nullable=False),
        sa.Column("category", sa.String(30), nullable=False),
        sa.Column("status", sa.String(20), default="OPEN", nullable=False),
        sa.Column("input_roster_version", sa.Integer(), nullable=False),
        sa.Column("need_summary", sa.Text(), nullable=True),
        sa.Column("missing_tags", sa.JSON(), nullable=True),
        sa.Column("analyzed_expert_ids", sa.JSON(), nullable=True),
        sa.Column("evidence", sa.Text(), nullable=True),
        sa.Column("supersedes_alert_id", sa.String(36), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "coverage_reviews",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("alert_id", sa.String(36), sa.ForeignKey("coverage_alerts.id"), nullable=False),
        sa.Column("conclusion", sa.String(30), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("reviewer_id", sa.String(36), nullable=False),
        sa.Column("input_version", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "notifications",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("activity_id", sa.String(36), nullable=True),
        sa.Column("notification_type", sa.String(40), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column("target_id", sa.String(36), nullable=True),
        sa.Column("is_read", sa.Boolean(), default=False, nullable=False),
        sa.Column("read_at", sa.String(40), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("activity_id", sa.String(36), nullable=True),
        sa.Column("actor_user_id", sa.String(36), nullable=True),
        sa.Column("action", sa.String(50), nullable=False),
        sa.Column("target_type", sa.String(50), nullable=True),
        sa.Column("target_id", sa.String(36), nullable=True),
        sa.Column("detail", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "outbox_events",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("event_type", sa.String(50), nullable=False),
        sa.Column("activity_id", sa.String(36), nullable=True),
        sa.Column("payload", sa.JSON(), nullable=True),
        sa.Column("dispatched", sa.Boolean(), default=False, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "operator_notes",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("activity_id", sa.String(36), sa.ForeignKey("activities.id"), nullable=False),
        sa.Column("activity_member_id", sa.String(36), sa.ForeignKey("activity_members.id"), nullable=False),
        sa.Column("author_id", sa.String(36), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "idempotency_records",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("idempotency_key", sa.String(100), unique=True, nullable=False),
        sa.Column("operation", sa.String(50), nullable=False),
        sa.Column("result_data", sa.Text(), nullable=True),
        sa.Column("status_code", sa.Integer(), default=200, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade():
    for table in [
        "idempotency_records", "operator_notes", "outbox_events", "audit_logs",
        "notifications", "coverage_reviews", "coverage_alerts", "ai_jobs",
        "ai_messages", "ai_sessions", "dev_sessions", "role_grants",
        "expert_participations", "expert_profiles", "review_decisions",
        "registration_snapshots", "registration_drafts", "member_contacts",
        "activity_members", "activities", "users",
    ]:
        op.drop_table(table)
