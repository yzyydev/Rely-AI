from pydantic import BaseModel, Field
from typing import List, Dict, Optional


class DecideRequest(BaseModel):
    """
    Request model for the /decide endpoint
    
    Attributes:
        prompt: XML content containing purpose, factors, decision resources and models
    """
    prompt: str = Field(..., description="XML content with purpose, factors, decision resources and models")


class BoardResponse(BaseModel):
    """
    Represents a single board model response
    
    Attributes:
        model: The name of the model (e.g., "gpt-4o", "claude-3.5-sonnet")
        path: The filesystem path where the response is stored
    """
    model: str = Field(..., description="Name of the board model")
    path: str = Field(..., description="Path to the model's response markdown file")


class DecideResponse(BaseModel):
    """
    Response model for the /decide endpoint
    
    Attributes:
        id: Unique identifier for the decision (UUID)
        status: Status of the decision process ("completed", "failed", etc.)
        board: List of board model responses with paths
        ceo_decision_path: Path to the CEO decision markdown file
        ceo_prompt: Path to the CEO prompt XML file
    """
    id: str = Field(..., description="Unique identifier for this decision")
    status: str = Field(..., description="Status of the decision process")
    board: List[BoardResponse] = Field(..., description="List of board model responses")
    ceo_decision_path: Optional[str] = Field(None, description="Path to the CEO decision markdown file")
    ceo_prompt: Optional[str] = Field(None, description="Path to the CEO prompt XML file")


class ErrorResponse(BaseModel):
    """
    Error response model
    
    Attributes:
        detail: Error detail message
        message: Optional additional error information
    """
    detail: str = Field(..., description="Error detail message")
    message: Optional[str] = Field(None, description="Additional error information")