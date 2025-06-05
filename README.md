# Rely AI Decision Evaluator Backend

An experimental parallel LLM system that fans-out requests to multiple LLM models and fans-in to a "CEO" model for evaluation.

## Overview

This FastAPI backend provides a stateless implementation of a multi-LLM evaluation system with the following workflow:

1. **Fan-out**: Concurrently calls multiple LLM "board members" using `asyncio.gather`
2. **Fan-in**: Aggregates all responses and passes them to a "CEO" model for final decision
3. **Persistence**: Stores all inputs, outputs and decisions as markdown files in a UUID-based directory

The system is completely stateless, with no database requirements. All persistence is handled through the filesystem.

## Features

- Concurrent API calls to multiple LLM providers (OpenAI, Anthropic)
- Stateless architecture with filesystem-based persistence
- Automatic UUID-based organization of output files
- RESTful API with Swagger documentation
- Request retry with exponential backoff for reliability
- Configurable CEO model selection
- Support for advanced model features:
  - OpenAI models with reasoning levels (`:low`, `:medium`, `:high`)
  - Anthropic models with thinking budgets (`:1k`, `:4k`, `:16k`, etc.)

## Requirements

- Python 3.9+
- FastAPI
- Uvicorn
- httpx (for async HTTP requests)
- pydantic
- OpenAI and Anthropic Python SDKs

## Installation

1. Clone the repository
2. Install the dependencies:

```bash
cd backend
pip install -r requirements.txt
```

3. Install the project in development mode (to make the `atoms` package importable):

```bash
pip install -e .
```

Alternatively, you can set the `PYTHONPATH` environment variable:

```bash
export PYTHONPATH=$PYTHONPATH:/path/to/rely_ai/backend
```

4. Set the required environment variables:

```bash
export OPENAI_API_KEY=sk-...
export ANTHROPIC_API_KEY=sk-...
export GEMINI_API_KEY=sk-...
export OUTPUT_DIR=/path/to/output  # Optional, defaults to /backend/output
```

5. Check if providers are correctly installed:

```bash
./check_providers.py
```

## Starting the Server

Start the server with Uvicorn:

```bash
uvicorn app.main:app --reload
```

The server will be available at http://localhost:8000 with Swagger documentation at http://localhost:8000/docs.

## Quick Start

The easiest way to test the system is to use the provided example script:

1. Start the server:

```bash
./start.sh
```

2. In another terminal, run the example script:

```bash
./example.py
```

This will send a sample request to the API, which includes a purpose, factors, decision resources, and models. The board models will analyze the request, and the CEO model will evaluate their responses to make a final decision.

## XML Format

The backend accepts XML input with the following structure:

```xml
<purpose>
    Description of the decision to be evaluated
</purpose>
<factors>
    1. Factor 1
    2. Factor 2
    ...
</factors>
<board-models>
    <model name="o4-mini:high" />
    <model name="gpt-4o" />
    <!-- up to N board models -->
</board-models>
<ceo-model name="claude-3-7-sonnet:4k" />
<decision-resources>
    Additional information relevant to the decision
</decision-resources>
```

### XML Elements

- The `purpose` element contains the main question or decision to evaluate
- The `factors` element lists key considerations
- Model specification:
  - `<board-models>`: List of models to use for independent analysis
  - `<ceo-model>`: Single model to use for final decision-making
- OpenAI reasoning models (o3, o4-mini, etc.) can include reasoning effort with `:low`, `:medium`, or `:high` suffix
- Anthropic claude-3-7-sonnet-20250219 model can include thinking budget with `:1k`, `:4k`, etc. suffix
- The `decision-resources` element provides additional context

## API Endpoints

### POST `/decide`

Accepts an XML payload containing:
- `purpose`: The decision question and context
- `factors`: Key factors to consider
- `models`: List of LLM models to use as board members (with optional CEO designation)
- `decision-resources`: Additional resources for making the decision

Example request:

```bash
curl -X POST http://localhost:8000/decide \
  -H 'Content-Type: application/json' \
  -d '{
    "prompt": "<purpose>Should we enter the EV market?</purpose><factors>1. Market growth\n2. Competition</factors><board-models><model name=\"o4-mini:high\" /><model name=\"gpt-4o\" /></board-models><ceo-model name=\"claude-3-7-sonnet:4k\" /><decision-resources>Industry reports show...</decision-resources>"
  }'
```

Example response:

```json
{
  "id": "0b68d7e8-...",
  "status": "completed",
  "board": [
    {"model": "o4-mini:high", "path": "/backend/output/.../board_o4-mini:high.md"},
    {"model": "claude-3-7-sonnet:4k", "path": "/backend/output/.../board_claude-3-7-sonnet:4k.md"}
  ],
  "ceo_decision_path": "/backend/output/.../ceo_decision.md",
  "ceo_prompt": "/backend/output/.../ceo_prompt.xml"
}
```

## Output Files

The system generates several output files for each decision:
- `/output/<uuid>/board_<model-name>.md` - Raw responses from each model
- `/output/<uuid>/ceo_decision.md` - Final markdown decision from the CEO model
- `/output/<uuid>/ceo_prompt.xml` - The prompt sent to the CEO model

## Configuration

The system can be configured through environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key for GPT models | - |
| `ANTHROPIC_API_KEY` | Anthropic API key for Claude models | - |
| `OUTPUT_DIR` | Directory for output files | `/backend/output` |
| `DEFAULT_CEO_MODEL` | Default model to use as CEO if none specified | `gpt-4o` |
| `HTTP_TIMEOUT` | Timeout for HTTP requests in seconds | `120` |
| `MAX_RETRIES` | Maximum retry attempts for failed requests | `3` |
| `HOST` | Host to bind the server to | `0.0.0.0` |
| `PORT` | Port to run the server on | `8000` |

## Testing

Run the tests with pytest:

```bash
pip install -r requirements-dev.txt
pytest
```

For specific test categories:

```bash
# Test XML parsing
pytest tests/test_xml_parsing.py

# Test LLM providers (needs providers installed)
pytest tests/test_llm_providers.py

# Test with coverage
pytest --cov=app
```

## LLM Provider Structure

The system uses a modular LLM provider structure from the `atoms.llm_providers` package:

- `openai.py` - Implements the OpenAI provider with support for reasoning suffixes (`:low`, `:medium`, `:high`)
- `anthropic.py` - Implements the Anthropic provider with support for thinking budgets (`:1k`, `:4k`, `:16k` etc.)

Each provider has a common interface:
- `prompt(text, model)` - Send a prompt to the model
- `list_models()` - List available models

## Architecture

```
Client  ── POST /decide ─▶  FastAPI Route
                             │ (validate)
                             ▼
                  async process_decision()            
                             │
             ┌───────────────┴───────────────┐
             ▼                               ▼  (fan-out)
    call_model(model-1) … call_model(model-N)    ≤— asyncio.gather
             │                               │
             └───────────────┬───────────────┘
                             ▼  (fan-in)
                   call_ceo_model(board_responses)
                             │
                             ▼
               write /output/<id>/*.md files
                             │
                             ▼
           JSON response { id, ceo_path }
```

## License

MIT
