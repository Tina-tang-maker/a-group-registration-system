from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio

from app.api.router import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.workers.ai_worker import run_ai_worker
    from app.workers.coverage_worker import run_coverage_scan

    ai_task = asyncio.create_task(run_ai_worker())
    coverage_task = asyncio.create_task(run_coverage_scan())

    yield

    ai_task.cancel()
    coverage_task.cancel()
    try:
        await ai_task
    except asyncio.CancelledError:
        pass
    try:
        await coverage_task
    except asyncio.CancelledError:
        pass


app = FastAPI(
    title="A组报名与资格管理 API",
    description="活动管理、学员/导师报名、运营审核、AI对话、覆盖提醒、跨组交接",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/health")
async def health():
    return {"status": "ok"}
