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
    <models>
        <model name="o4-mini:medium" />
        <model name="claude-3-7-sonnet:2k" ceo="true" />
    </models>
    <decision-resources>
    Computer Price: $5,000
    Current Budget: $10,000
    Monthly Income: $6,000
    Monthly Expenses: $4,000
    Expected Useful Life: 5 years
    </decision-resources>
    </root>"""
    
    # Parse the XML
    purpose, factors, resources, models, ceo_model = parse_xml_input(xml_content)
    
    # Check that purpose was extracted
    assert "purchasing a high-end computer" in purpose
    
    # Check that factors were extracted
    assert "Return on Investment" in factors
    assert "Cash Flow Management" in factors
    assert "Future Resale Value" in factors
    
    # Check that models with suffixes were extracted correctly
    assert "o4-mini:medium" in models
    assert "claude-3-7-sonnet:2k" in models
    
    # Check that CEO model was identified
    assert ceo_model == "claude-3-7-sonnet:2k"
    
    # Check resources
    assert "Computer Price: $5,000" in resources

def test_parse_xml_missing_models():
    """Test that an error is raised when models are missing"""
    xml_content = """<root>
    <purpose>Test purpose</purpose>
    <factors>Test factors</factors>
    <decision-resources>Test resources</decision-resources>
    </root>"""
    
    # Parsing should raise a ValueError due to missing models
    with pytest.raises(ValueError, match="No models specified"):
        parse_xml_input(xml_content)

def test_parse_xml_malformed():
    """Test that an error is raised for malformed XML"""
    xml_content = """
    <purpose>Test purpose</purpose>
    <factors>Test factors</factors
    <models><model name="test-model" /></models>
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
    <models>
        <model name="o4-mini:medium" />
        <model name="claude-3-7-sonnet:2k" />
    </models>
    <decision-resources>Test resources</decision-resources>
    </root>"""
    
    # Parse the XML
    purpose, factors, resources, models, ceo_model = parse_xml_input(xml_content)
    
    # No CEO model should be identified
    assert ceo_model is None