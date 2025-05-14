import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    """
    Application settings loaded from environment variables
    """
    # API Keys
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None
    
    # Paths
    output_dir: str = "/Users/yzyy/Projects/rely_ai/backend/output"
    
    # LLM configuration
    default_ceo_model: str = "gpt-4o"
    
    # HTTP client configuration
    http_timeout: int = 120  # seconds
    max_retries: int = 3
    
    # Server configuration
    host: str = "0.0.0.0"
    port: int = 8000
    
    # API configuration
    api_prefix: str = "/api/v1"
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore"  # This will ignore extra fields in the environment
    }
    
    def validate(self):
        """
        Validate the configuration
        """
        # Try to load API keys from environment if not set
        if not self.openai_api_key:
            self.openai_api_key = os.getenv("OPENAI_API_KEY")
            
        if not self.anthropic_api_key:
            self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
            
        if not self.gemini_api_key:
            self.gemini_api_key = os.getenv("GEMINI_API_KEY")
            
        # Create output directory if it doesn't exist
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)
        
        # Check API keys and warn if still not set
        if not self.openai_api_key:
            logger.warning("OPENAI_API_KEY is not set. OpenAI models will not be available.")
        
        if not self.anthropic_api_key:
            logger.warning("ANTHROPIC_API_KEY is not set. Anthropic models will not be available.")
            
        if not self.gemini_api_key:
            logger.warning("GEMINI_API_KEY is not set. Gemini models will not be available.")
            
        # Additionally attempt to load other environment variables
        env_output_dir = os.getenv("OUTPUT_DIR")
        if env_output_dir:
            self.output_dir = env_output_dir
            
        env_ceo_model = os.getenv("DEFAULT_CEO_MODEL")
        if env_ceo_model:
            self.default_ceo_model = env_ceo_model
            
        return self

# Create and validate settings
settings = Settings().validate()