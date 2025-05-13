import pytest
from unittest.mock import patch, MagicMock
import sys
import os

# Add path for atoms package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Try importing LLM providers directly
try:
    from atoms.llm_providers import openai, anthropic
    PROVIDERS_AVAILABLE = True
except ImportError:
    PROVIDERS_AVAILABLE = False

from app.utils import parse_model_name, validate_model_name

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