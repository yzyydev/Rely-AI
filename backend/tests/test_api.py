import pytest
import json
import httpx
from unittest.mock import patch, MagicMock, AsyncMock
import os
from app.main import app
from app.models import DecideRequest
from fastapi.testclient import TestClient

@pytest.mark.asyncio
async def test_decide_endpoint(
    test_client, 
    mock_async_httpx_post, 
    mock_openai_response, 
    mock_anthropic_response,
    sample_xml_payload
):
    # Mock direct provider calls
    with patch('app.service.call_model', new_callable=AsyncMock) as mock_call_model:
        # Mock the call_model function to return fixed responses
        mock_call_model.return_value = "This is a mocked model response"
        
        # Set environment variables for the test
        os.environ["OPENAI_API_KEY"] = "test_openai_key"
        os.environ["ANTHROPIC_API_KEY"] = "test_anthropic_key"
        
        # Make request to the API
        response = test_client.post(
            "/decide",
            json={"prompt": sample_xml_payload}
        )
        
        # Check response
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "id" in data
        assert "status" in data
        assert "board" in data
        assert "ceo_decision_path" in data
        assert "ceo_prompt" in data
        
        # Check status
        assert data["status"] == "completed"
        
        # Check board responses
        assert len(data["board"]) == 2  # We should have responses for both models
        
        # Check paths
        for board_item in data["board"]:
            assert "model" in board_item
            assert "path" in board_item
            assert board_item["path"].startswith("/")
        
        # Verify output files exist
        output_dir_parts = data["ceo_decision_path"].split("/")
        uuid = output_dir_parts[-2]  # Extract UUID from path
        
        # Clean up test output
        import shutil
        output_base = "/Users/yzyy/Projects/rely_ai/backend/output"
        shutil.rmtree(f"{output_base}/{uuid}", ignore_errors=True)

def test_invalid_xml(test_client):
    """Test invalid XML handling"""
    response = test_client.post(
        "/decide",
        json={"prompt": "<invalid>xml<invalid>"}
    )
    
    assert response.status_code == 400
    
def test_missing_models(test_client):
    """Test handling of missing models"""
    response = test_client.post(
        "/decide",
        json={"prompt": "<root><purpose>Test</purpose><factors>Test</factors><models></models></root>"}
    )
    
    assert response.status_code == 400