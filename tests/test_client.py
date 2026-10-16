"""Test Hermes Agent API client."""

from unittest.mock import AsyncMock, MagicMock

import aiohttp
import pytest

from custom_components.hermes_agent.client import (
    CannotConnect,
    HermesAgentClient,
    InvalidAuth,
    ModelNotFoundError,
)


@pytest.mark.asyncio
async def test_client_headers_and_urls():
    """Test client initialization and headers."""
    session = MagicMock()
    client = HermesAgentClient(session, "http://127.0.0.1:8642", "secret_key")
    assert client.root_url == "http://127.0.0.1:8642"
    assert client.v1_url == "http://127.0.0.1:8642/v1"
    headers = client._get_headers()
    assert headers["Authorization"] == "Bearer secret_key"
    assert headers["Accept"] == "application/json"


@pytest.mark.asyncio
async def test_client_get_health_success():
    """Test successful health check."""
    session = MagicMock()
    mock_resp = AsyncMock()
    mock_resp.status = 200
    mock_resp.json = AsyncMock(return_value={"status": "ok", "version": "1.0.0"})
    session.get.return_value.__aenter__.return_value = mock_resp

    client = HermesAgentClient(session, "http://127.0.0.1:8642")
    data = await client.async_check_health()
    assert data["status"] == "ok"


@pytest.mark.asyncio
async def test_client_get_health_unauthorized():
    """Test 401 raises InvalidAuth."""
    session = MagicMock()
    mock_resp = AsyncMock()
    mock_resp.status = 401
    session.get.return_value.__aenter__.return_value = mock_resp

    client = HermesAgentClient(session, "http://127.0.0.1:8642", "bad_key")
    with pytest.raises(InvalidAuth):
        await client.async_check_health()


@pytest.mark.asyncio
async def test_client_get_detailed_health():
    """Test detailed health fetching."""
    session = MagicMock()
    mock_resp = AsyncMock()
    mock_resp.status = 200
    mock_resp.json = AsyncMock(
        return_value={
            "status": "healthy",
            "state": "idle",
            "active_agents": 2,
            "jobs_count": 3,
            "skills_count": 5,
        }
    )
    session.get.return_value.__aenter__.return_value = mock_resp

    client = HermesAgentClient(session, "http://127.0.0.1:8642")
    data = await client.async_get_health_detailed()
    assert data["status"] == "healthy"
    assert data["active_agents"] == 2


@pytest.mark.asyncio
async def test_client_get_models():
    """Test fetching model list."""
    session = MagicMock()
    mock_resp = AsyncMock()
    mock_resp.status = 200
    mock_resp.json = AsyncMock(
        return_value={
            "data": [
                {"id": "hermes-agent"},
                {"id": "hermes-3-llama-3.1-8b"},
            ]
        }
    )
    session.get.return_value.__aenter__.return_value = mock_resp

    client = HermesAgentClient(session, "http://127.0.0.1:8642")
    models = await client.async_get_models()
    assert "hermes-agent" in models
    assert "hermes-3-llama-3.1-8b" in models


@pytest.mark.asyncio
async def test_client_chat_completion_success():
    """Test chat completion invocation."""
    session = MagicMock()
    mock_resp = AsyncMock()
    mock_resp.status = 200
    mock_resp.json = AsyncMock(
        return_value={
            "id": "chatcmpl_123",
            "choices": [{"message": {"role": "assistant", "content": "Hello!"}}],
        }
    )
    session.post.return_value.__aenter__.return_value = mock_resp

    client = HermesAgentClient(session, "http://127.0.0.1:8642")
    res = await client.async_chat_completion(
        messages=[{"role": "user", "content": "Hi"}]
    )
    assert res["id"] == "chatcmpl_123"
    assert res["choices"][0]["message"]["content"] == "Hello!"


@pytest.mark.asyncio
async def test_client_chat_completion_model_not_found():
    """Test 404 raises ModelNotFoundError."""
    session = MagicMock()
    mock_resp = AsyncMock()
    mock_resp.status = 404
    session.post.return_value.__aenter__.return_value = mock_resp

    client = HermesAgentClient(session, "http://127.0.0.1:8642")
    with pytest.raises(ModelNotFoundError):
        await client.async_chat_completion(
            messages=[{"role": "user", "content": "Hi"}],
            model="non-existent-model",
        )


@pytest.mark.asyncio
async def test_client_sessions_and_jobs():
    """Test session and job helpers."""
    session = MagicMock()
    mock_resp = AsyncMock()
    mock_resp.status = 200
    mock_resp.json = AsyncMock(return_value=[{"id": "sess_1", "title": "Test"}])
    session.get.return_value.__aenter__.return_value = mock_resp

    client = HermesAgentClient(session, "http://127.0.0.1:8642")
    sessions = await client.async_get_sessions()
    assert len(sessions) == 1
    assert sessions[0]["id"] == "sess_1"

    jobs = await client.async_get_jobs()
    assert len(jobs) == 1


@pytest.mark.asyncio
async def test_client_connection_error():
    """Test network error wraps into CannotConnect."""
    session = MagicMock()
    session.get.side_effect = aiohttp.ClientError("Connection refused")

    client = HermesAgentClient(session, "http://127.0.0.1:8642")
    with pytest.raises(CannotConnect):
        await client.async_check_health()
