import os
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import logging

# Setup logging
logger = logging.getLogger(__name__)

def parse_xml_input(xml_content: str) -> Tuple[str, str, str, List[str], Optional[str]]:
    """
    Parse XML input to extract purpose, factors, resources, models, and CEO model.
    
    Args:
        xml_content: XML string containing decision request
        
    Returns:
        Tuple of (purpose, factors, resources, models, ceo_model)
        
    Raises:
        ET.ParseError: If XML is malformed
        ValueError: If required elements are missing
    """
    try:
        # Wrap the content in a root element if it doesn't have one
        if not xml_content.strip().startswith("<?xml") and not xml_content.strip().startswith("<root"):
            wrapped_xml = f"<root>{xml_content}</root>"
        else:
            wrapped_xml = xml_content
            
        root = ET.fromstring(wrapped_xml)
        
        # If we wrapped the XML, the actual elements will be children of root
        if root.tag == "root":
            elements = root
        else:
            elements = root
        
        # Extract purpose
        purpose_elem = elements.find('purpose')
        purpose = purpose_elem.text.strip() if purpose_elem is not None and purpose_elem.text else ""
        
        # Extract factors
        factors_elem = elements.find('factors')
        factors = factors_elem.text.strip() if factors_elem is not None and factors_elem.text else ""
        
        # Extract models
        models = []
        ceo_model = None
        models_elem = elements.find('models')
        if models_elem is not None:
            for model_elem in models_elem.findall('model'):
                model_name = model_elem.get('name')
                is_ceo = model_elem.get('ceo')
                
                if model_name:
                    models.append(model_name)
                    if is_ceo and is_ceo.lower() == 'true':
                        ceo_model = model_name
        
        # Extract decision resources
        resources_elem = elements.find('decision-resources')
        resources = resources_elem.text.strip() if resources_elem is not None and resources_elem.text else ""
        
        if not models:
            raise ValueError("No models specified in the request")
            
        return purpose, factors, resources, models, ceo_model
        
    except ET.ParseError as e:
        logger.error(f"XML parsing error: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Error parsing XML input: {str(e)}")
        raise ValueError(f"Error parsing XML input: {str(e)}")

def validate_model_name(model_name: str) -> bool:
    """
    Validate if a model name is supported
    
    Args:
        model_name: Name of the model to validate
        
    Returns:
        True if the model is supported, False otherwise
    """
    # The new provider structure supports more flexible model naming
    # OpenAI models include gpt-*, o3*, o4* with or without reasoning suffix (:low, :medium, :high)
    # Anthropic models include claude-* with or without thinking suffix (:1k, :4k, :16k or specific numbers)
    
    # Check for OpenAI models
    if model_name.startswith(("gpt-", "o3", "o4")):
        # Strip any reasoning suffix if present
        base_model = model_name.split(":")[0] 
        return True
    
    # Check for Anthropic models
    if model_name.startswith("claude-"):
        # Strip any thinking suffix if present
        base_model = model_name.split(":")[0]
        return True
    
    return False

def construct_board_prompt(purpose: str, factors: str, resources: str) -> str:
    """
    Construct the prompt for board models.
    
    Args:
        purpose: The purpose text
        factors: The factors text
        resources: The decision resources text
        
    Returns:
        Formatted board prompt XML
    """
    return f"""
<purpose>{purpose}</purpose>
<factors>{factors}</factors>
<decision-resources>{resources}</decision-resources>
"""

def construct_ceo_prompt(purpose: str, factors: str, board_responses: List[Dict[str, str]]) -> str:
    """
    Construct the CEO prompt with board responses.
    
    Args:
        purpose: The purpose text
        factors: The factors text
        board_responses: List of dictionaries with model_name and response
        
    Returns:
        CEO prompt XML
    """
    original_question = f"{purpose}\n\n{factors}"
    
    board_decisions_xml = ""
    for response in board_responses:
        board_decisions_xml += f"""
    <board-response>
        <model-name>{response['model_name']}</model-name>
        <response>{response['response']}</response>
    </board-response>
"""
    
    ceo_prompt = f"""
<purpose>
    You are a CEO of a company. You are given a list of responses from your board of directors. Your job is to take in the original question prompt, and each of the board members' responses, and choose the best direction for your company.
</purpose>
<instructions>
    <instruction>Each board member has proposed an answer to the question posed in the prompt.</instruction>
    <instruction>Given the original question prompt, and each of the board members' responses, choose the best answer.</instruction>
    <instruction>Tally the votes of the board members, choose the best direction, and explain why you chose it.</instruction>
    <instruction>To preserve anonymity, we will use model names instead of real names of your board members. When responding, use the model names in your response.</instruction>
    <instruction>As a CEO, you breakdown the decision into several categories including: risk, reward, timeline, and resources. In addition to these guiding categories, you also consider the board members' expertise and experience. As a bleeding edge CEO, you also invent new dimensions of decision making to help you make the best decision for your company.</instruction>
    <instruction>Your final CEO response should be in markdown format with a comprehensive explanation of your decision. Start the top of the file with a title that says "CEO Decision", include a table of contents, briefly describe the question/problem at hand then dive into several sections. One of your first sections should be a quick summary of your decision, then breakdown each of the boards decisions into sections with your commentary on each. Where we lead into your decision with the categories of your decision making process, and then we lead into your final decision.</instruction>
</instructions>
<original-question>{original_question}</original-question>
<board-decisions>
{board_decisions_xml}
</board-decisions>
"""
    
    return ceo_prompt

def ensure_output_directory(base_dir: str, decision_id: str) -> Path:
    """
    Ensure the output directory exists for a given decision ID
    
    Args:
        base_dir: Base output directory
        decision_id: Unique decision ID
        
    Returns:
        Path object for the decision directory
    """
    output_dir = Path(base_dir) / decision_id
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir

def sanitize_xml(xml_content: str) -> str:
    """
    Sanitize XML content to prevent XML injection attacks
    
    Args:
        xml_content: Raw XML content
        
    Returns:
        Sanitized XML content
    """
    # Replace XML special characters
    sanitized = (xml_content
                .replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;')
                .replace("'", '&apos;'))
    
    return sanitized

def parse_model_name(model_name: str) -> Tuple[str, Optional[str], Optional[str]]:
    """
    Parse a model name to extract provider, base name, and any suffix
    
    Args:
        model_name: Full model name with optional suffix (e.g., gpt-4o, claude-3.5-sonnet:4k)
        
    Returns:
        Tuple of (provider, base_model, suffix)
        provider: 'openai' or 'anthropic'
        base_model: The base model name without suffix
        suffix: Any suffix (:low, :medium, :high, :1k, :4k, etc.) or None
    """
    # Extract suffix if present
    parts = model_name.split(":", 1)
    base_name = parts[0]
    suffix = parts[1] if len(parts) > 1 else None
    
    # Determine provider
    if base_name.startswith(("gpt-", "o3", "o4")):
        provider = "openai"
    elif base_name.startswith("claude-"):
        provider = "anthropic"
    else:
        provider = None
        
    return provider, base_name, suffix