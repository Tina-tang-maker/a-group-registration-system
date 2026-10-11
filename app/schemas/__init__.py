from app.schemas.common import Page, PageQuery, DeletedResult
from app.schemas.identity import Persona, SelectPersona, CurrentActor, ContextQuery
from app.schemas.activity import (
    ActivityCreate, ActivityPatch, ActivityView, ActivitySummary,
    PublicActivitySummary, VersionInput,
)
from app.schemas.registration import (
    JoinInput, DraftPatch, SubmitInput, RegistrationView,
    HistoryCopyInput, ReasonInput, SnapshotView, BasicInfo,
)
from app.schemas.review import (
    ReviewInput, ContactPatch, NoteInput, NoteView,
    AdminSubmitInput, ManualRegistrationInput, ContactView,
    AdminRegistrationView, RegistrationSummary,
)
from app.schemas.manual import (
    ManualExpertInput, ManualDraftPatch, ManualSubmitInput,
    CapacityUpdateInput, CapacityUpdateView, MemberParticipationChanged,
)
from app.schemas.ai import (
    AiSessionInput, MessageInput, MessageAccepted,
    DossierJobInput, JobView, AiSessionView, AiMessageView,
)
from app.schemas.coverage import CoverageJobInput, CoverageAlertView, CoverageReviewInput
from app.schemas.matching import MatchingInputResponse, MemberView, EligibleExpert, StudentNeed
from app.schemas.notification import NotificationView, ReminderInput, ReminderResult
from app.schemas.audit import AuditView, DashboardView
