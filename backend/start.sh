#!/bin/bash
# Start the Rely AI Decision Evaluator Backend

# Check for required environment variables
if [ -z "$OPENAI_API_KEY" ]; then
  echo "Error: OPENAI_API_KEY environment variable must be set."
  echo "Run: export OPENAI_API_KEY=sk-..."
  exit 1
fi

if [ -z "$ANTHROPIC_API_KEY" ]; then
  echo "Error: ANTHROPIC_API_KEY environment variable must be set."
  echo "Run: export ANTHROPIC_API_KEY=sk-..."
  exit 1
fi

# Create output directory if it doesn't exist
mkdir -p "$(dirname "$0")/output"

# Start the server
echo "Starting Rely AI Decision Evaluator Backend..."
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000