"""Regression tests for admin API prefix compatibility."""

from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_admin_alias_endpoints_under_api_prefix(async_client, admin_token, security_headers, stub_job_queue):
    """Admin routes should be reachable via the /api/admin prefix for the frontend."""

    headers = security_headers(token=admin_token)
    for path in (
        "/api/admin/jobs/stats",
        "/api/admin/health/system",
        "/api/admin/health/performance",
    ):
        response = await async_client.get(path, headers=headers)
        assert response.status_code == 200, f"{path} failed: {response.text}"
        assert response.json(), f"{path} returned an empty payload"


@pytest.mark.asyncio
async def test_admin_alias_endpoints_require_auth(async_client, stub_job_queue):
    """The /api/admin prefixed routes should enforce authentication."""

    for path in (
        "/api/admin/jobs/stats",
        "/api/admin/health/system",
        "/api/admin/health/performance",
    ):
        response = await async_client.get(path)
        assert response.status_code in (401, 403), f"{path} unexpectedly allowed anonymous access"
