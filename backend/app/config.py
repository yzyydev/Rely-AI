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
    openai_api_key: Optional[str] = os.getenv("OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = os.getenv("ANTHROPIC_API_KEY")
    
    # Paths
    output_dir: str = os.getenv("OUTPUT_DIR", "/Users/yzyy/Projects/rely_ai/backend/output")
    
    # LLM configuration
    default_ceo_model: str = os.getenv("DEFAULT_CEO_MODEL", "gpt-4o")
    
    # HTTP client configuration
    http_timeout: int = int(os.getenv("HTTP_TIMEOUT", "120"))  # seconds
    max_retries: int = int(os.getenv("MAX_RETRIES", "3"))
    
    # Server configuration
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8000"))
    
    # API configuration
    api_prefix: str = "/api/v1"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
    
    def validate(self):
        """
        Validate the configuration
        """
        # Create output directory if it doesn't exist
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)
        
        # Check API keys
        if not self.openai_api_key:
            logger.warning("OPENAI_API_KEY is not set. OpenAI models will not be available.")
        
        if not self.anthropic_api_key:
            logger.warning("ANTHROPIC_API_KEY is not set. Anthropic models will not be available.")
            
        return self

# Create and validate settings
settings = Settings().validate()