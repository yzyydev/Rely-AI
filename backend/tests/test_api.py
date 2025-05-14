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
    mock_anthropic_response
):
    """Test the decide endpoint with the required XML format"""
    # Create test XML with board-models and ceo-model format
    xml_content = """<root>
    <purpose>Test purpose</purpose>
    <factors>Test factors</factors>
    <board-models>
        <model name="gpt-4o" />
        <model name="o4-mini:high" />
    </board-models>
    <ceo-model name="claude-3-7-sonnet:2k" />
    <decision-resources>Test resources</decision-resources>
    </root>"""
    
    # Mock the service methods
    with patch('app.service.generate_board_decisions', new_callable=AsyncMock) as mock_board, \
         patch('app.service.generate_ceo_decision', new_callable=AsyncMock) as mock_ceo:
         
        # Set up mock return values
        mock_board.return_value = [
            {"model_name": "gpt-4o", "response": "Board response 1"},
            {"model_name": "o4-mini:high", "response": "Board response 2"}
        ]
        mock_ceo.return_value = "CEO decision from claude-3-7-sonnet"
        
        # Set API keys for the test
        os.environ["OPENAI_API_KEY"] = "test_openai_key"
        os.environ["ANTHROPIC_API_KEY"] = "test_anthropic_key"
        
        # Make sure we don't have any old feature flags set
        if "USE_SEPARATE_BOARD_CEO_MODELS" in os.environ:
            del os.environ["USE_SEPARATE_BOARD_CEO_MODELS"]
        
        # Make request to the API
        response = test_client.post(
            "/decide",
            json={"prompt": xml_content}
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
        models = [board["model"] for board in data["board"]]
        assert "gpt-4o" in models
        assert "o4-mini:high" in models
        
        # Verify the generate_board_decisions function was called
        mock_board.assert_called_once()
        # Verify the generate_ceo_decision function was called with the correct CEO model
        mock_ceo.assert_called_once()
        assert mock_ceo.call_args[0][0] == "claude-3-7-sonnet:2k"
        
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
    """Test handling of missing board-models"""
    response = test_client.post(
        "/decide",
        json={"prompt": "<root><purpose>Test</purpose><factors>Test</factors><ceo-model name=\"test-model\"/></root>"}
    )
    
    assert response.status_code == 400