import uuid
import logging
import sys
import os
from pathlib import Path
from typing import Dict, Optional, List
import xml.etree.ElementTree as ET

# Add the parent directory to the Python path so that atoms can be imported
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.models import DecideRequest, DecideResponse, BoardResponse, ErrorResponse
from app.utils import (
    parse_xml_input, 
    construct_board_prompt, 
    construct_ceo_prompt, 
    ensure_output_directory
)
from app.service import call_model, process_board_responses, generate_board_decisions, generate_ceo_decision

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# In-memory decision registry
class DecisionStatus:
    def __init__(self, id: str, purpose: str, models: List[str]):
        self.id = id
        self.purpose = purpose
        self.models = models
        self.board_responses: Dict[str, str] = {}
        self.ceo_decision: Optional[str] = None
        self.status = "pending"
        self.output_dir = ensure_output_directory(settings.output_dir, id)

# Global registry
DECISIONS: Dict[str, DecisionStatus] = {}

# Initialize FastAPI with versioned API prefix
app = FastAPI(
    title="Rely AI Decision Evaluator",
    description="Parallel LLM evaluation system that fans-out to multiple models and fans-in to a CEO model",
    version="0.1.0",
    docs_url=None,
    redoc_url=None,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handler
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "message": str(exc)}
    )

@app.exception_handler(ET.ParseError)
async def xml_parse_error_handler(request: Request, exc: ET.ParseError):
    logger.error(f"XML parsing error: {str(exc)}")
    return JSONResponse(
        status_code=400,
        content={"detail": "Invalid XML format", "message": str(exc)}
    )

@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    logger.error(f"Value error: {str(exc)}")
    return JSONResponse(
        status_code=400,
        content={"detail": "Validation error", "message": str(exc)}
    )

# Custom Swagger UI
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url="/openapi.json",
        title="Rely AI Decision Evaluator API",
        swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@4.15.5/swagger-ui-bundle.js",
        swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@4.15.5/swagger-ui.css",
    )

@app.get("/", tags=["Health"])
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy", 
        "service": "Rely AI Decision Evaluator",
        "version": "0.1.0"
    }

@app.post("/decide", response_model=DecideResponse, tags=["Decisions"], responses={400: {"model": ErrorResponse}})
async def decide(request: DecideRequest):
    """
    Process a decision with parallel LLM calls to board models and a follow-up CEO model call.
    
    This endpoint:
    1. Parses the XML input to extract purpose, factors, resources, and models
    2. Fans-out calls to all board models in parallel
    3. Fans-in with a CEO model call that evaluates all board responses
    4. Writes all responses and the CEO decision to the filesystem
    5. Returns paths to all generated files
    
    The connection remains open until the entire process completes (blocking).
    """
    try:
        # Generate UUID for this decision
        decision_id = str(uuid.uuid4())
        logger.info(f"Processing new decision request: {decision_id}")
        
        # Parse XML input
        try:
            purpose, factors, resources, board_models, ceo_model = parse_xml_input(request.prompt)
        except ET.ParseError as e:
            # Handle XML parsing errors explicitly
            logger.error(f"XML parsing error: {str(e)}")
            raise HTTPException(status_code=400, detail=f"Invalid XML format: {str(e)}")
        except ValueError as e:
            # Handle validation errors
            logger.error(f"Validation error: {str(e)}")
            raise HTTPException(status_code=400, detail=str(e))
        
        # If CEO model is not specified, use the default
        if not ceo_model:
            ceo_model = settings.default_ceo_model
            logger.info(f"Using default CEO model: {ceo_model}")
        
        # Create decision status
        decision = DecisionStatus(id=decision_id, purpose=purpose, models=board_models)
        DECISIONS[decision_id] = decision
        
        # Create output directory
        output_dir = ensure_output_directory(settings.output_dir, decision_id)
        
        # Stage 1: Fan-out - Generate board decisions in parallel
        logger.info(f"Starting parallel model calls for {len(board_models)} board models")
        board_responses = await generate_board_decisions(board_models, purpose, factors, resources)
        logger.info(f"Completed all board model calls")
        
        # Store board responses
        board_paths = []
        
        for response in board_responses:
            model_name = response["model_name"]
            model_response = response["response"]
            
            # Save board response to file
            board_file_path = output_dir / f"board_{model_name}.md"
            with open(board_file_path, "w") as f:
                f.write(model_response)
                
            # Update decision status
            decision.board_responses[model_name] = model_response
            
            # Record path for response
            relative_path = str(board_file_path.relative_to(Path(settings.output_dir).parent))
            board_paths.append(BoardResponse(
                model=model_name, 
                path=f"/{relative_path}"
            ))
            
            logger.info(f"Saved board response for {model_name}")
        
        # Stage 2: Fan-in - Generate CEO decision
        logger.info(f"Generating CEO decision with {len(board_responses)} board responses")
        ceo_prompt = construct_ceo_prompt(purpose, factors, board_responses)
        
        # Save CEO prompt to file
        ceo_prompt_path = output_dir / "ceo_prompt.xml"
        with open(ceo_prompt_path, "w") as f:
            f.write(ceo_prompt)
        
        # Stage 3: Call CEO model
        logger.info(f"Calling CEO model: {ceo_model}")
        ceo_decision = await generate_ceo_decision(ceo_model, purpose, factors, board_responses)
        
        # Save CEO decision to file
        ceo_decision_path = output_dir / "ceo_decision.md"
        with open(ceo_decision_path, "w") as f:
            f.write(ceo_decision)
        
        # Update decision status
        decision.ceo_decision = ceo_decision
        decision.status = "completed"
        
        relative_ceo_path = str(ceo_decision_path.relative_to(Path(settings.output_dir).parent))
        relative_ceo_prompt_path = str(ceo_prompt_path.relative_to(Path(settings.output_dir).parent))
        
        logger.info(f"Decision process completed: {decision_id}")
        
        # Return complete response
        return DecideResponse(
            id=decision.id,
            status=decision.status,
            board=board_paths,
            ceo_decision_path=f"/{relative_ceo_path}",
            ceo_prompt=f"/{relative_ceo_prompt_path}"
        )
    
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app", 
        host=settings.host, 
        port=settings.port, 
        reload=True
    )