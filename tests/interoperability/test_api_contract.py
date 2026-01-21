import re

import pytest


@pytest.mark.asyncio
@pytest.mark.interoperability
async def test_openapi_contract_with_frontend_endpoints(http_client):
    response = await http_client.get("/openapi.json")

    assert response.status_code == 200
    schema = response.json()

    paths = list(schema.get("paths", {}).keys())

    expected_templates = [
        "/api/v1/accounts/login",
        "/api/v1/accounts/refresh",
        "/api/v1/accounts/password-reset/request",
        "/api/v1/accounts/password-reset/confirm",
        "/api/v1/accounts/change-password",
        "/api/v1/users/me",
        "/api/v1/users/all",
        "/api/v1/users/create",
        "/api/v1/users/update/{id}",
        "/api/v1/users/desactivate/{id}",
        "/api/v1/users/activate/{id}",
        "/api/v1/athletes/all",
        "/api/v1/athletes/register-unl",
        "/api/v1/athletes/register-minor",
        "/api/v1/athletes/update/{id}",
        "/api/v1/athletes/desactivate/{id}",
        "/api/v1/athletes/activate/{id}",
        "/api/v1/attendances/bulk",
        "/api/v1/attendances/by-date",
        "/api/v1/attendances/summary",
        "/api/v1/representatives/all",
        "/api/v1/representatives/{id}",
        "/api/v1/representatives/by-dni/{dni}",
        "/api/v1/representatives/create",
        "/api/v1/representatives/update/{id}",
        "/api/v1/representatives/deactivate/{id}",
        "/api/v1/representatives/activate/{id}",
        "/api/v1/reports/attendance",
        "/api/v1/reports/tests",
        "/api/v1/reports/statistics",
        "/api/v1/evaluations/",
        "/api/v1/evaluations/{id}",
        "/api/v1/evaluations/user/{user_id}",
        "/api/v1/sprint-tests/",
        "/api/v1/endurance-tests/",
        "/api/v1/yoyo-tests/",
        "/api/v1/technical-assessments/",
        "/api/v1/statistics/overview",
        "/api/v1/statistics/attendance",
        "/api/v1/statistics/tests",
        "/api/v1/statistics/athlete/{id}",
        "/api/v1/statistics/athlete/{id}/sports-stats",
    ]

    missing = []
    for template in expected_templates:
        normalized = template.rstrip("/")
        if "{" in template:
            pattern = "^" + re.sub(r"\{[^/]+\}", r"[^/]+", normalized) + "/?$"
            if not any(re.match(pattern, path) for path in paths):
                missing.append(template)
        else:
            if not any(path.rstrip("/") == normalized for path in paths):
                missing.append(template)

    assert not missing, f"Faltan endpoints en OpenAPI: {missing}"
