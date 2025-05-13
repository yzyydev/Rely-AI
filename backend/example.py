#!/usr/bin/env python3
"""
Example script to demonstrate using the Rely AI Decision Evaluator Backend
"""
import requests
import json
import os
import sys
from pathlib import Path

# Check if API keys are set
if not os.environ.get("OPENAI_API_KEY") or not os.environ.get("ANTHROPIC_API_KEY"):
    print("Error: OPENAI_API_KEY and ANTHROPIC_API_KEY environment variables must be set.")
    print("Run: export OPENAI_API_KEY=sk-... ANTHROPIC_API_KEY=sk-...")
    sys.exit(1)

# Read the sample XML
sample_xml_path = Path(__file__).parent / "sample_request.xml"
with open(sample_xml_path, "r") as f:
    xml_content = f.read()

# Make the API request
url = "http://localhost:8000/decide"
payload = {"prompt": xml_content}
headers = {"Content-Type": "application/json"}

print("Sending request to the Rely AI Decision Evaluator...")
response = requests.post(url, json=payload, headers=headers)

# Check the response
if response.status_code == 200:
    result = response.json()
    print("Decision process completed successfully!")
    print(f"Decision ID: {result['id']}")
    print("\nBoard Responses:")
    for board in result["board"]:
        print(f"- {board['model']}: {board['path']}")
    
    print(f"\nCEO Decision: {result['ceo_decision_path']}")
    
    # Print path to view result
    ceo_path = result['ceo_decision_path'].lstrip('/')
    print(f"\nTo view the CEO decision, run:")
    print(f"cat {ceo_path}")
else:
    print(f"Error: {response.status_code}")
    print(response.text)