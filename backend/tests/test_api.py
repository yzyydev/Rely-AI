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
    <ceo-model name="claude-3-5-sonnet-20240620" />
    <decision-resources>Test resources</decision-resources>
    </root>"""
    
    # Mock the httpx response for LLM API calls
    async def mock_response(url, *args, **kwargs):
        mock_response = httpx.Response(200, json=mock_anthropic_response if "anthropic" in url else mock_openai_response)
        return mock_response
    
    mock_async_httpx_post.side_effect = mock_response
    
    # Mock the service methods directly at the lowest level
    with patch('app.service.call_model_with_retry', new_callable=AsyncMock) as mock_call_model:
         
        # Set up mock return values for the call_model_with_retry function
        # This will be called for each board model and the CEO model
        mock_call_model.side_effect = [
            "Board response 1",  # for gpt-4o
            "Board response 2",  # for o4-mini:high
            "CEO decision from claude-3-5-sonnet-20240620"  # for CEO model
        ]
        
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
        
        # Verify the call_model_with_retry function was called for both board models and the CEO model
        assert mock_call_model.call_count == 3
        
        # Check the calls were made with the correct model names
        call_args_list = mock_call_model.call_args_list
        assert call_args_list[0][0][0] == "gpt-4o"  # First call for first board model
        assert call_args_list[1][0][0] == "o4-mini:high"  # Second call for second board model
        assert call_args_list[2][0][0] == "claude-3-5-sonnet-20240620"  # Third call for CEO model
        
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