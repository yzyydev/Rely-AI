import pytest
import os
from app.utils import parse_xml_input

def test_parse_xml_with_suffixed_models():
    """Test parsing XML with models that have suffixes"""
    # Create test XML directly (avoiding file dependency)
    xml_content = """<root>
    <purpose>I want to rigorously evaluate whether purchasing a high-end computer under current budget constraints is a sound decision</purpose>
    <factors>
        1. Return on Investment 
        2. Cash Flow Management 
        3. Future Resale Value
    </factors>
    <board-models>
        <model name="o4-mini:medium" />
        <model name="gpt-4o" />
    </board-models>
    <ceo-model name="claude-3-7-sonnet:2k" />
    <decision-resources>
    Computer Price: $5,000
    Current Budget: $10,000
    Monthly Income: $6,000
    Monthly Expenses: $4,000
    Expected Useful Life: 5 years
    </decision-resources>
    </root>"""
    
    # Parse the XML
    purpose, factors, resources, board_models, ceo_model = parse_xml_input(xml_content)
    
    # Check that purpose was extracted
    assert "purchasing a high-end computer" in purpose
    
    # Check that factors were extracted
    assert "Return on Investment" in factors
    assert "Cash Flow Management" in factors
    assert "Future Resale Value" in factors
    
    # Check that models with suffixes were extracted correctly
    assert "o4-mini:medium" in board_models
    assert "gpt-4o" in board_models
    
    # Check that CEO model was identified
    assert ceo_model == "claude-3-7-sonnet:2k"
    
    # Check resources
    assert "Computer Price: $5,000" in resources


def test_parse_xml_missing_models():
    """Test that an error is raised when board-models are missing"""
    xml_content = """<root>
    <purpose>Test purpose</purpose>
    <factors>Test factors</factors>
    <ceo-model name="claude-3-7-sonnet:2k" />
    <decision-resources>Test resources</decision-resources>
    </root>"""
    
    # Parsing should raise a ValueError due to missing board-models
    with pytest.raises(ValueError, match="Missing required <board-models>"):
        parse_xml_input(xml_content)

def test_parse_xml_malformed():
    """Test that an error is raised for malformed XML"""
    xml_content = """
    <purpose>Test purpose</purpose>
    <factors>Test factors</factors
    <board-models><model name="test-model" /></board-models>
    <decision-resources>Test resources</decision-resources>
    """
    
    # Parsing should raise an ET.ParseError due to malformed XML
    with pytest.raises(Exception):
        parse_xml_input(xml_content)

def test_parse_xml_no_ceo():
    """Test parsing XML with no CEO model designated"""
    xml_content = """<root>
    <purpose>Test purpose</purpose>
    <factors>Test factors</factors>
    <board-models>
        <model name="o4-mini:medium" />
        <model name="gpt-4o" />
    </board-models>
    <decision-resources>Test resources</decision-resources>
    </root>"""
    
    # Parse the XML
    purpose, factors, resources, board_models, ceo_model = parse_xml_input(xml_content)
    
    # No CEO model should be identified
    assert ceo_model is None
    
