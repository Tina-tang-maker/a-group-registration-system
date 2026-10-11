import pytest
from httpx import AsyncClient
from app.tests.conftest import create_test_app, override_get_db, test_db_session
from app.database import Base, engine
from app.models import *


@pytest.fixture(autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.mark.anyio
async def test_create_manual_expert():
    app = create_test_app()
    async with AsyncClient(app=app, base_url="http://test") as client:
        dev_r = await client.post("/api/v1/dev/sessions", json={
            "persona_id": "persona-operator-1",
            "activity_id": "seed-activity-1",
            "role": "OPERATOR"
        })
        assert dev_r.status_code == 200
        token = dev_r.json()["token"]

        r = await client.post(
            "/api/v1/manual/activities/seed-activity-1/experts",
            json={
                "name": "测试导师",
                "phone": "13800138000",
                "branch": "BEIJING",
                "industries": ["TECH"],
                "topics": ["CAREER"]
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        assert r.status_code == 201
        data = r.json()
        assert "activity_member_id" in data
        assert data["role"] == "EXPERT"


@pytest.mark.anyio
async def test_patch_manual_draft():
    app = create_test_app()
    async with AsyncClient(app=app, base_url="http://test") as client:
        dev_r = await client.post("/api/v1/dev/sessions", json={
            "persona_id": "persona-operator-1",
            "activity_id": "seed-activity-1",
            "role": "OPERATOR"
        })
        token = dev_r.json()["token"]

        create_r = await client.post(
            "/api/v1/manual/activities/seed-activity-1/experts",
            json={
                "name": "测试导师",
                "phone": "13800138000",
                "branch": "BEIJING"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        member_id = create_r.json()["activity_member_id"]

        r = await client.patch(
            f"/api/v1/manual/activities/seed-activity-1/members/{member_id}/draft",
            json={
                "sections": {
                    "experience": "10年技术管理经验",
                    "supported_problems": "团队管理、技术架构",
                    "boundaries": "每周最多2次咨询"
                }
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        assert r.status_code == 200


@pytest.mark.anyio
async def test_submit_manual_expert():
    app = create_test_app()
    async with AsyncClient(app=app, base_url="http://test") as client:
        dev_r = await client.post("/api/v1/dev/sessions", json={
            "persona_id": "persona-operator-1",
            "activity_id": "seed-activity-1",
            "role": "OPERATOR"
        })
        token = dev_r.json()["token"]

        create_r = await client.post(
            "/api/v1/manual/activities/seed-activity-1/experts",
            json={
                "name": "测试导师",
                "phone": "13800138000",
                "branch": "BEIJING"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        member_id = create_r.json()["activity_member_id"]

        await client.patch(
            f"/api/v1/manual/activities/seed-activity-1/members/{member_id}/draft",
            json={
                "sections": {
                    "experience": "10年技术管理经验",
                    "supported_problems": "团队管理、技术架构",
                    "boundaries": "每周最多2次咨询"
                }
            },
            headers={"Authorization": f"Bearer {token}"}
        )

        r = await client.post(
            f"/api/v1/manual/activities/seed-activity-1/members/{member_id}/submit",
            json={
                "confirmation_basis": "运营确认资料完整",
                "expected_version": 2
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        assert r.status_code == 200
        data = r.json()
        assert data["submission_status"] == "SUBMITTED"


@pytest.mark.anyio
async def test_update_expert_capacity():
    app = create_test_app()
    async with AsyncClient(app=app, base_url="http://test") as client:
        dev_r = await client.post("/api/v1/dev/sessions", json={
            "persona_id": "persona-operator-1",
            "activity_id": "seed-activity-1",
            "role": "OPERATOR"
        })
        token = dev_r.json()["token"]

        create_r = await client.post(
            "/api/v1/manual/activities/seed-activity-1/experts",
            json={
                "name": "测试导师",
                "phone": "13800138000",
                "branch": "BEIJING"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        member_id = create_r.json()["activity_member_id"]

        r = await client.patch(
            f"/api/v1/activities/seed-activity-1/members/{member_id}/capacity",
            json={
                "capacity_override": 5,
                "reason": "该导师经验丰富，增加容量",
                "expected_version": 1
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        assert r.status_code == 200
        data = r.json()
        assert data["capacity_override"] == 5
        assert data["effective_capacity"] == 5
        assert data["version"] == 2


@pytest.mark.anyio
async def test_end_participation():
    app = create_test_app()
    async with AsyncClient(app=app, base_url="http://test") as client:
        dev_r = await client.post("/api/v1/dev/sessions", json={
            "persona_id": "persona-operator-1",
            "activity_id": "seed-activity-1",
            "role": "OPERATOR"
        })
        token = dev_r.json()["token"]

        create_r = await client.post(
            "/api/v1/manual/activities/seed-activity-1/experts",
            json={
                "name": "测试导师",
                "phone": "13800138000",
                "branch": "BEIJING"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        member_id = create_r.json()["activity_member_id"]

        r = await client.post(
            f"/api/v1/activities/seed-activity-1/members/{member_id}/end",
            json={"reason": "导师主动退出"},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert r.status_code == 200
        data = r.json()
        assert data["participation_status"] == "INACTIVE"
        assert data["reason"] == "导师主动退出"


@pytest.mark.anyio
async def test_withdraw_member():
    app = create_test_app()
    async with AsyncClient(app=app, base_url="http://test") as client:
        dev_r = await client.post("/api/v1/dev/sessions", json={
            "persona_id": "persona-operator-1",
            "activity_id": "seed-activity-1",
            "role": "OPERATOR"
        })
        token = dev_r.json()["token"]

        create_r = await client.post(
            "/api/v1/manual/activities/seed-activity-1/experts",
            json={
                "name": "测试导师",
                "phone": "13800138000",
                "branch": "BEIJING"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        member_id = create_r.json()["activity_member_id"]

        r = await client.post(
            f"/api/v1/activities/seed-activity-1/members/{member_id}/withdraw",
            json={"reason": "学员申请退出"},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert r.status_code == 200
        data = r.json()
        assert data["participation_status"] == "WITHDRAWN"
        assert data["reason"] == "学员申请退出"
