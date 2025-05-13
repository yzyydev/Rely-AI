import pytest
from app.utils import (
    parse_xml_input,
    construct_board_prompt,
    construct_ceo_prompt,
    parse_model_name,
    validate_model_name
)
import xml.etree.ElementTree as ET
from pathlib import Path
import os

def test_parse_xml_input():
    # Test valid XML
    valid_xml = """<root>
    <purpose>Test purpose</purpose>
    <factors>Test factors</factors>
    <models>
        <model name="gpt-4o" />
        <model name="claude-3.5-sonnet" />
    </models>
    <decision-resources>Test resources</decision-resources>
    </root>"""
    
    purpose, factors, resources, models, ceo_model = parse_xml_input(valid_xml)
    
    assert purpose == "Test purpose"
    assert factors == "Test factors"
    assert resources == "Test resources"
    assert models == ["gpt-4o", "claude-3.5-sonnet"]
    assert ceo_model is None
    
    # Test unwrapped XML (should be auto-wrapped)
    unwrapped_xml = """
    <purpose>Test purpose</purpose>
    <factors>Test factors</factors>
    <models>
        <model name="gpt-4o" />
        <model name="claude-3.5-sonnet" ceo="true" />
    </models>
    <decision-resources>Test resources</decision-resources>
    """
    
    purpose, factors, resources, models, ceo_model = parse_xml_input(unwrapped_xml)
    
    assert purpose == "Test purpose"
    assert factors == "Test factors"
    assert resources == "Test resources"
    assert models == ["gpt-4o", "claude-3.5-sonnet"]
    assert ceo_model == "claude-3.5-sonnet"
    
    # Test missing models
    invalid_xml = """<root>
    <purpose>Test purpose</purpose>
    <factors>Test factors</factors>
    <models></models>
    <decision-resources>Test resources</decision-resources>
    </root>"""
    
    with pytest.raises(ValueError):
        parse_xml_input(invalid_xml)

def test_construct_board_prompt():
    purpose = "Test purpose"
    factors = "Test factors"
    resources = "Test resources"
    
    prompt = construct_board_prompt(purpose, factors, resources)
    
    assert "<purpose>Test purpose</purpose>" in prompt
    assert "<factors>Test factors</factors>" in prompt
    assert "<decision-resources>Test resources</decision-resources>" in prompt

def test_construct_ceo_prompt():
    purpose = "Test purpose"
    factors = "Test factors"
    board_responses = [
        {"model_name": "gpt-4o", "response": "Test response 1"},
        {"model_name": "claude-3.5-sonnet", "response": "Test response 2"}
    ]
    
    prompt = construct_ceo_prompt(purpose, factors, board_responses)
    
    assert "<original-question>Test purpose\n\nTest factors</original-question>" in prompt
    assert "<model-name>gpt-4o</model-name>" in prompt
    assert "<response>Test response 1</response>" in prompt
    assert "<model-name>claude-3.5-sonnet</model-name>" in prompt
    assert "<response>Test response 2</response>" in prompt

def test_parse_model_name():
    # Test OpenAI models
    provider, base, suffix = parse_model_name("gpt-4o")
    assert provider == "openai"
    assert base == "gpt-4o" 
    assert suffix is None
    
    provider, base, suffix = parse_model_name("o4-mini:high")
    assert provider == "openai"
    assert base == "o4-mini"
    assert suffix == "high"
    
    # Test Anthropic models
    provider, base, suffix = parse_model_name("claude-3.5-sonnet")
    assert provider == "anthropic"
    assert base == "claude-3.5-sonnet"
    assert suffix is None
    
    provider, base, suffix = parse_model_name("claude-3-7-sonnet:4k")
    assert provider == "anthropic"
    assert base == "claude-3-7-sonnet"
    assert suffix == "4k"
    
    # Test unknown model
    provider, base, suffix = parse_model_name("unknown-model")
    assert provider is None
    assert base == "unknown-model"
    assert suffix is None

def test_validate_model_name():
    # Valid models
    assert validate_model_name("gpt-4o")
    assert validate_model_name("o4-mini:high")
    assert validate_model_name("claude-3.5-sonnet")
    assert validate_model_name("claude-3-7-sonnet:4k")
    
    # Invalid models
    assert not validate_model_name("unknown-model")