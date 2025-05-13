import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import sys
import os
import asyncio

# Add path for atoms package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Try importing LLM providers directly
try:
    from atoms.llm_providers import openai, anthropic
    PROVIDERS_AVAILABLE = True
except ImportError:
    PROVIDERS_AVAILABLE = False

from app.utils import parse_model_name, validate_model_name
from app.service import generate_board_decisions, generate_ceo_decision, call_model, process_board_responses

@pytest.mark.skipif(not PROVIDERS_AVAILABLE, reason="LLM providers not available")
def test_openai_parse_reasoning_suffix():
    """Test parsing reasoning suffixes for OpenAI models"""
    # Valid reasoning model + suffix
    base, effort = openai.parse_reasoning_suffix("o4-mini:high")
    assert base == "o4-mini"
    assert effort == "high"
    
    # Valid reasoning model without suffix
    base, effort = openai.parse_reasoning_suffix("o4-mini")
    assert base == "o4-mini"
    assert effort == ""
    
    # Invalid reasoning model with suffix
    base, effort = openai.parse_reasoning_suffix("gpt-4o:high")
    assert base == "gpt-4o:high"  # Returns the whole string as base
    assert effort == ""

@pytest.mark.skipif(not PROVIDERS_AVAILABLE, reason="LLM providers not available")
def test_anthropic_parse_thinking_suffix():
    """Test parsing thinking suffixes for Anthropic models"""
    # Valid thinking model + k suffix
    base, budget = anthropic.parse_thinking_suffix("claude-3-7-sonnet-20250219:4k")
    assert base == "claude-3-7-sonnet-20250219"
    assert budget == 4096  # 4k = 4 * 1024
    
    # Valid thinking model + numeric suffix
    base, budget = anthropic.parse_thinking_suffix("claude-3-7-sonnet-20250219:2000")
    assert base == "claude-3-7-sonnet-20250219"
    assert budget == 2000


@pytest.mark.skipif(not PROVIDERS_AVAILABLE, reason="LLM providers not available")
def test_list_models():
    """Test listing models from providers"""
    # Mock the API calls
    with patch('atoms.llm_providers.openai.client.models.list') as mock_openai_list, \
         patch('atoms.llm_providers.anthropic.client.models.list') as mock_anthropic_list:
        
        # Setup mock responses
        mock_openai_model = MagicMock()
        mock_openai_model.id = "o4-mini"
        mock_openai_list.return_value = MagicMock(data=[mock_openai_model])
        
        mock_anthropic_model = MagicMock()
        mock_anthropic_model.id = "claude-3-7-sonnet"
        mock_anthropic_list.return_value = MagicMock(data=[mock_anthropic_model])
        
        # Test OpenAI model listing
        openai_models = openai.list_models()
        assert "o4-mini" in openai_models
        
        # Test Anthropic model listing
        anthropic_models = anthropic.list_models()
        assert "claude-3-7-sonnet" in anthropic_models

def test_utils_parse_model_name():
    """Test parsing model names in utils module"""
    # OpenAI models
    provider, base, suffix = parse_model_name("o4-mini:high")
    assert provider == "openai"
    assert base == "o4-mini"
    assert suffix == "high"
    
    # Anthropic models
    provider, base, suffix = parse_model_name("claude-3-7-sonnet:4k")
    assert provider == "anthropic"
    assert base == "claude-3-7-sonnet"
    assert suffix == "4k"
    
    # No suffix
    provider, base, suffix = parse_model_name("gpt-4o")
    assert provider == "openai"
    assert base == "gpt-4o"
    assert suffix is None
    
    # Unknown provider
    provider, base, suffix = parse_model_name("unknown-model")
    assert provider is None
    assert base == "unknown-model"
    assert suffix is None

def test_utils_validate_model_name():
    """Test validating model names in utils module"""
    # Valid OpenAI models
    assert validate_model_name("gpt-4o")
    assert validate_model_name("o4-mini:high")
    
    # Valid Anthropic models
    assert validate_model_name("claude-3-7-sonnet:4k")
    
    # Invalid models
    assert not validate_model_name("invalid-model")

@pytest.mark.asyncio
async def test_call_model_with_roles():
    """Test that the call_model function passes the correct system prompts based on role"""
    with patch('app.service.openai.prompt', return_value="Test response") as mock_openai_prompt:
        # Test board member role
        await call_model("gpt-4o", "Test prompt", is_ceo=False)
        # Check that the first argument contains the board member system prompt
        args = mock_openai_prompt.call_args[0]
        assert "You are a board member providing a detailed analysis" in args[0]
        
        # Reset the mock for the CEO test
        mock_openai_prompt.reset_mock()
        
        # Test CEO role
        await call_model("gpt-4o", "Test prompt", is_ceo=True)
        # Check that the first argument contains the CEO system prompt
        args = mock_openai_prompt.call_args[0]
        assert "You are the CEO making a final decision" in args[0]

@pytest.mark.asyncio
async def test_generate_board_decisions():
    """Test that generate_board_decisions correctly calls process_board_responses"""
    with patch('app.service.process_board_responses', new_callable=AsyncMock) as mock_process:
        mock_process.return_value = [
            {"model_name": "model1", "response": "Board response 1"},
            {"model_name": "model2", "response": "Board response 2"}
        ]
        
        result = await generate_board_decisions(
            board_models=["model1", "model2"],
            purpose="Test purpose",
            factors="Test factors",
            resources="Test resources"
        )
        
        # Check that the function was called with the correct parameters
        mock_process.assert_called_once()
        assert len(result) == 2
        assert result[0]["model_name"] == "model1"
        assert result[1]["model_name"] == "model2"

@pytest.mark.asyncio
async def test_generate_ceo_decision():
    """Test that generate_ceo_decision correctly calls call_model_with_retry"""
    with patch('app.service.call_model_with_retry', new_callable=AsyncMock) as mock_call:
        mock_call.return_value = "CEO decision"
        
        board_responses = [
            {"model_name": "model1", "response": "Board response 1"},
            {"model_name": "model2", "response": "Board response 2"}
        ]
        
        result = await generate_ceo_decision(
            ceo_model="ceo-model",
            purpose="Test purpose",
            factors="Test factors",
            board_responses=board_responses
        )
        
        # Check that the function was called with the correct parameters
        mock_call.assert_called_once()
        assert mock_call.call_args[0][0] == "ceo-model"  # ceo_model
        assert mock_call.call_args[1]["is_ceo"] is True  # is_ceo parameter
        assert result == "CEO decision"