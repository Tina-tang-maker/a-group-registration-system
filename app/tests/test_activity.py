import pytest
from httpx import AsyncClient


async def _get_operator_token(client: AsyncClient) -> str:
    resp = await client.post("/api/v1/dev/sessions", json={
        "persona_id": "persona-operator-1",
    })
    return resp.headers.get("x-dev-token")


@pytest.mark.asyncio
async def test_create_and_list_activity(client: AsyncClient):
    token = await _get_operator_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    create_resp = await client.post(
        "/api/v1/activities",
        json={"name": "测试活动", "description": "描述"},
        headers=headers,
    )
    assert create_resp.status_code == 201
    activity = create_resp.json()
    assert activity["name"] == "测试活动"
    assert activity["status"] == "DRAFT"
    assert activity["version"] == 1

    list_resp = await client.get("/api/v1/activities", headers=headers)
    assert list_resp.status_code == 200
    assert list_resp.json()["total"] >= 1


@pytest.mark.asyncio
async def test_activity_publish_requires_time_order(client: AsyncClient):
    token = await _get_operator_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    create_resp = await client.post(
        "/api/v1/activities",
        json={"name": "无时间活动"},
        headers=headers,
    )
    activity = create_resp.json()

    pub_resp = await client.post(
        f"/api/v1/activities/{activity['activity_id']}/publication",
        json={"expected_version": activity["version"]},
        headers=headers,
    )
    assert pub_resp.status_code == 422


@pytest.mark.asyncio
async def test_activity_patch_version_conflict(client: AsyncClient):
    token = await _get_operator_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    create_resp = await client.post(
        "/api/v1/activities",
        json={"name": "版本测试"},
        headers=headers,
    )
    activity = create_resp.json()

    patch_resp = await client.patch(
        f"/api/v1/activities/{activity['activity_id']}",
        json={
            "name": "更新名称",
            "reason": "测试修改",
            "expected_version": 999,
        },
        headers=headers,
    )
    assert patch_resp.status_code == 409
