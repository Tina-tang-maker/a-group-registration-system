import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_public_activities_empty(client: AsyncClient):
    response = await client.get("/api/v1/public/activities")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["items"] == []


@pytest.mark.asyncio
async def test_dev_personas(client: AsyncClient):
    response = await client.get("/api/v1/dev/personas")
    assert response.status_code == 200
    personas = response.json()
    assert len(personas) == 3
    names = [p["name"] for p in personas]
    assert "张同学" in names
    assert "李导师" in names
    assert "王运营" in names


@pytest.mark.asyncio
async def test_create_session_and_get_context(client: AsyncClient):
    response = await client.post("/api/v1/dev/sessions", json={
        "persona_id": "persona-operator-1",
        "activity_id": None,
        "role": None,
    })
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == "persona-operator-1"
    assert data["name"] == "王运营"
    token = response.headers.get("x-dev-token")
    assert token is not None

    context_resp = await client.get(
        "/api/v1/me/context",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert context_resp.status_code == 200
    assert context_resp.json()["user_id"] == "persona-operator-1"


@pytest.mark.asyncio
async def test_unauthorized_access(client: AsyncClient):
    response = await client.get("/api/v1/me/context")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_create_activity_requires_operator(client: AsyncClient):
    student_session = await client.post("/api/v1/dev/sessions", json={
        "persona_id": "persona-student-1",
    })
    token = student_session.headers.get("x-dev-token")

    response = await client.post(
        "/api/v1/activities",
        json={"name": "Test Activity"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403
