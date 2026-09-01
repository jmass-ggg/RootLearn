"""Integration tests for root gap API endpoints.

These tests verify that the root gap endpoint is properly registered
and has the correct structure.

Task: 11.4
Requirements: 18.1
"""
import uuid

import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app


@pytest.mark.asyncio
async def test_get_root_gap_endpoint_exists():
    """Test that GET /api/v1/sessions/{session_id}/root-gap exists."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        fake_session_id = uuid.uuid4()
        fake_user_id = uuid.uuid4()
        
        response = await client.get(
            f"/api/v1/sessions/{fake_session_id}/root-gap",
            params={"user_id": str(fake_user_id)},
        )
        
        # Should return 404 (session not found) not 405 (method not allowed)
        # This confirms the endpoint exists and is properly registered
        assert response.status_code == 404
        data = response.json()
        # Error format is nested in detail.error
        assert "detail" in data
        assert "error" in data["detail"]
        assert data["detail"]["error"]["code"] == "session_not_found"


@pytest.mark.asyncio
async def test_root_gap_endpoint_has_correct_path():
    """Verify root gap endpoint is registered with correct path."""
    from fastapi.routing import APIRoute
    from app.routes import root_gap
    
    root_gap_routes = []
    for route in root_gap.router.routes:
        if isinstance(route, APIRoute):
            methods = list(route.methods)
            root_gap_routes.append((methods, route.path))
    
    # Check that we have the root gap route
    assert len(root_gap_routes) >= 1, f"Expected at least 1 root gap route, found {len(root_gap_routes)}"
    
    # Extract paths
    paths = [path for _, path in root_gap_routes]
    
    # Check for the required endpoint
    assert any("/root-gap" in path for path in paths), f"Missing /root-gap endpoint in {paths}"
    
    # Check HTTP methods
    methods_by_path = {path: methods for methods, path in root_gap_routes}
    
    for path, methods in methods_by_path.items():
        if "/root-gap" in path:
            assert "GET" in methods, f"/root-gap should accept GET, got {methods}"


@pytest.mark.asyncio
async def test_root_gap_endpoint_requires_user_id_parameter():
    """Test that root gap endpoint requires user_id query parameter."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        fake_session_id = uuid.uuid4()
        
        # Call without user_id parameter
        response = await client.get(
            f"/api/v1/sessions/{fake_session_id}/root-gap",
        )
        
        # Should return 422 (validation error for missing required parameter)
        assert response.status_code == 422
        data = response.json()
        
        # FastAPI validation error structure
        assert "detail" in data
