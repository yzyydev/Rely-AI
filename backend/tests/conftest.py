import pytest
from fastapi.testclient import TestClient
from app.main import app
import os
import httpx
from unittest.mock import patch, AsyncMock

@pytest.fixture
def test_client():
    """
    Create a test client for FastAPI app
    """
    return TestClient(app)

@pytest.fixture
def mock_openai_response():
    """
    Mock response from OpenAI API
    """
    return {
        "id": "chatcmpl-123",
        "object": "chat.completion",
        "created": 1677858242,
        "model": "gpt-4o",
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": "This is a mocked OpenAI response."
                },
                "index": 0,
                "finish_reason": "stop"
            }
        ],
        "usage": {
            "prompt_tokens": 13,
            "completion_tokens": 7,
            "total_tokens": 20
        }
    }

@pytest.fixture
def mock_anthropic_response():
    """
    Mock response from Anthropic API
    """
    return {
        "id": "msg_123",
        "type": "message",
        "model": "claude-3-7-sonnet",
        "content": [
            {
                "type": "text",
                "text": "This is a mocked Anthropic response."
            }
        ],
        "role": "assistant",
        "stop_reason": "end_turn",
        "usage": {
            "input_tokens": 13,
            "output_tokens": 7
        }
    }

@pytest.fixture
def mock_async_httpx_post():
    """
    Mock the httpx.AsyncClient.post method
    """
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        # Configuring the mock will be done in the tests
        yield mock_post

@pytest.fixture
def sample_xml_payload():
    """
    Sample XML payload for testing
    """
    return """<root>
    <purpose>Test purpose</purpose>
    <factors>
        1. Factor 1
        2. Factor 2
    </factors>
    <board-models>
        <model name="gpt-4o" />
        <model name="o4-mini:high" />
    </board-models>
    <ceo-model name="claude-3-7-sonnet" />
    <decision-resources>
        Some test resources
    </decision-resources>
    </root>"""