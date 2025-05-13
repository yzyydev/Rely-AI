import asyncio
import logging
import random
import sys
from typing import List, Dict, Any, Optional
from fastapi import HTTPException

from app.config import settings
from app.utils import validate_model_name

# Import LLM providers
try:
    from atoms.llm_providers import openai, anthropic
    LLM_PROVIDERS_AVAILABLE = True
except ImportError:
    LLM_PROVIDERS_AVAILABLE = False
    logging.getLogger(__name__).error("LLM providers not available. Make sure the atoms package is installed.")

# Setup logging
logger = logging.getLogger(__name__)

class ModelCallRetryError(Exception):
    """Exception raised when a model call fails after all retries"""
    pass

async def call_model_with_retry(model_name: str, prompt: str, max_retries: int = None) -> str:
    """
    Call an LLM model with the given prompt, with retry logic
    
    Args:
        model_name: Name of the model to call
        prompt: XML prompt to send to the model
        max_retries: Maximum number of retries (defaults to settings.max_retries)
        
    Returns:
        Model response text
        
    Raises:
        ValueError: If model is not supported
        ModelCallRetryError: If all retries fail
    """
    if max_retries is None:
        max_retries = settings.max_retries
        
    if not validate_model_name(model_name):
        raise ValueError(f"Unsupported model: {model_name}")
    
    retry_count = 0
    last_error = None
    
    # Exponential backoff parameters
    base_delay = 1  # seconds
    max_delay = 32  # seconds
    
    while retry_count <= max_retries:
        try:
            return await call_model(model_name, prompt)
        except Exception as e:
            last_error = e
            retry_count += 1
            
            if retry_count > max_retries:
                logger.error(f"Failed to call model {model_name} after {max_retries} retries")
                break
                
            # Calculate delay with exponential backoff and jitter
            delay = min(base_delay * (2 ** (retry_count - 1)), max_delay)
            delay = delay * (0.5 + 0.5 * random.random())  # Add jitter
            
            logger.warning(f"Call to model {model_name} failed. Retrying in {delay:.2f} seconds... ({retry_count}/{max_retries})")
            await asyncio.sleep(delay)
    
    # If we get here, all retries have failed
    error_msg = f"Failed to call model {model_name} after {max_retries} retries: {str(last_error)}"
    logger.error(error_msg)
    raise ModelCallRetryError(error_msg)

async def call_model(model_name: str, prompt: str) -> str:
    """
    Call an LLM model with the given prompt.
    
    Args:
        model_name: Name of the model to call (e.g., "gpt-4o", "claude-3.5-sonnet")
        prompt: XML prompt to send to the model
        
    Returns:
        Model response text
        
    Raises:
        ValueError: If API keys are not set or model is unsupported
        HTTPException: If API call fails
    """
    logger.info(f"Calling model: {model_name}")
    
    if not LLM_PROVIDERS_AVAILABLE:
        raise ValueError("LLM providers not available. Make sure the atoms package is installed.")
    
    try:
        # Use OpenAI provider for gpt-*, o3*, o4* models
        if model_name.startswith(("gpt-", "o3", "o4")):
            logger.info(f"Using OpenAI provider for model: {model_name}")
            
            # Add board member system prompt
            system_prompt = "You are a board member providing a detailed analysis."
            full_prompt = f"{system_prompt}\n\n{prompt}"
            
            # Call OpenAI provider synchronously - converting to async pattern
            result = await asyncio.to_thread(openai.prompt, full_prompt, model_name)
            return result
                
        # Use Anthropic provider for claude-* models
        elif model_name.startswith("claude-"):
            logger.info(f"Using Anthropic provider for model: {model_name}")
            
            # Add board member system prompt
            system_prompt = "You are a board member providing a detailed analysis."
            full_prompt = f"{system_prompt}\n\n{prompt}"
            
            # Call Anthropic provider synchronously - converting to async pattern
            result = await asyncio.to_thread(anthropic.prompt, full_prompt, model_name)
            return result
        else:
            raise ValueError(f"Unsupported model: {model_name}")
    
    except Exception as e:
        logger.error(f"Error calling model {model_name}: {str(e)}")
        raise

async def process_board_responses(models: List[str], board_prompt: str) -> List[Dict[str, str]]:
    """
    Process board responses in parallel.
    
    Args:
        models: List of model names to call
        board_prompt: Prompt to send to each model
        
    Returns:
        List of model responses
    """
    # Fan-out: Make parallel LLM calls to all board models
    board_tasks = [call_model_with_retry(model, board_prompt) for model in models]
    
    try:
        board_results = await asyncio.gather(*board_tasks)
    except Exception as e:
        logger.error(f"Error in parallel model calls: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error in parallel model calls: {str(e)}")
    
    # Format results
    formatted_results = []
    for model, response in zip(models, board_results):
        formatted_results.append({
            "model_name": model,
            "response": response
        })
    
    return formatted_results

def list_available_models() -> Dict[str, List[str]]:
    """
    List all available models from all providers
    
    Returns:
        Dictionary with provider names as keys and lists of model names as values
    """
    if not LLM_PROVIDERS_AVAILABLE:
        logger.warning("LLM providers not available. Returning empty model list.")
        return {"openai": [], "anthropic": []}
    
    try:
        openai_models = openai.list_models()
        anthropic_models = anthropic.list_models()
        
        return {
            "openai": openai_models,
            "anthropic": anthropic_models
        }
    except Exception as e:
        logger.error(f"Error listing available models: {str(e)}")
        return {"openai": [], "anthropic": []}