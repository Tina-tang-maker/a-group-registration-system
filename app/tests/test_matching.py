import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_matching_input_contract(client: AsyncClient):
    """Test that matching-input returns the correct contract structure"""
    token_resp = await client.post("/api/v1/dev/sessions", json={
        "persona_id": "persona-operator-1",
        "activity_id": "seed-activity-1",
        "role": "OPERATOR",
    })
    token = token_resp.headers.get("x-dev-token")
    headers = {"Authorization": f"Bearer {token}"}

    response = await client.get(
        "/api/v1/internal/activities/seed-activity-1/matching-input",
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()

    assert "activity" in data
    assert "members" in data
    assert "eligible_experts" in data
    assert "student_needs" in data

    activity = data["activity"]
    assert "activity_id" in activity
    assert "name" in activity
    assert "capacity_max" in activity
    assert "max_choices_per_student" in activity
    assert "expert_response_deadline" in activity

    for member in data["members"]:
        assert "activity_id" in member
        assert "activity_member_id" in member
        assert "role" in member
        assert "display_name" in member
        assert member["review_status"] == "APPROVED"

    for expert in data["eligible_experts"]:
        assert "activity_id" in expert
        assert "activity_member_id" in expert
        assert "sections" in expert
        assert "experience" in expert["sections"]
        assert "supported_problems" in expert["sections"]
        assert "boundaries" in expert["sections"]
        assert expert["available"] is True

    for student in data["student_needs"]:
        assert "activity_id" in student
        assert "activity_member_id" in student
        assert "sections" in student
        assert "background" in student["sections"]
        assert "problem" in student["sections"]
        assert "expected_help" in student["sections"]

    assert "user_id" not in str(data)
    assert "phone" not in str(data)
    assert "wechat" not in str(data)
