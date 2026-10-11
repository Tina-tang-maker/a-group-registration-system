from fastapi import APIRouter
from app.api.dev import router as dev_router
from app.api.activities import router as activities_router
from app.api.public import router as public_router
from app.api.registration import router as registration_router
from app.api.admin import router as admin_router
from app.api.manual import router as manual_router
from app.api.participation import router as participation_router
from app.api.ai import router as ai_router
from app.api.coverage import router as coverage_router
from app.api.matching import router as matching_router
from app.api.notifications import router as notifications_router
from app.api.audit import router as audit_router

api_router = APIRouter()

api_router.include_router(dev_router)
api_router.include_router(public_router)
api_router.include_router(activities_router)
api_router.include_router(registration_router)
api_router.include_router(admin_router)
api_router.include_router(manual_router)
api_router.include_router(participation_router)
api_router.include_router(ai_router)
api_router.include_router(coverage_router)
api_router.include_router(matching_router)
api_router.include_router(notifications_router)
api_router.include_router(audit_router)
