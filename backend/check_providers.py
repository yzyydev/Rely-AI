#!/usr/bin/env python3
"""
Check if LLM providers are correctly installed and can be imported
"""
import sys
import os

# Add the current directory to the path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

def check_providers():
    """Check if providers can be imported and return status for each"""
    results = {
        "openai": False,
        "anthropic": False,
        "atoms_package": False
    }
    
    # Check if atoms package can be imported
    try:
        import atoms
        results["atoms_package"] = True
        print(f"✅ atoms package imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import atoms package: {e}")
    
    # Check if providers can be imported
    if results["atoms_package"]:
        try:
            from atoms.llm_providers import openai
            results["openai"] = True
            print(f"✅ OpenAI provider imported successfully")
            print(f"   - OpenAI SDK version: {openai.__name__}")
        except ImportError as e:
            print(f"❌ Failed to import OpenAI provider: {e}")
        
        try:
            from atoms.llm_providers import anthropic
            results["anthropic"] = True
            print(f"✅ Anthropic provider imported successfully")
            print(f"   - Anthropic SDK version: {anthropic.__name__}")
        except ImportError as e:
            print(f"❌ Failed to import Anthropic provider: {e}")
    
    # Check provider API keys
    if results["openai"]:
        openai_key = os.environ.get("OPENAI_API_KEY")
        if openai_key:
            print(f"✅ OPENAI_API_KEY is set")
        else:
            print(f"❌ OPENAI_API_KEY is not set")
    
    if results["anthropic"]:
        anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
        if anthropic_key:
            print(f"✅ ANTHROPIC_API_KEY is set")
        else:
            print(f"❌ ANTHROPIC_API_KEY is not set")
    
    # Overall status
    if all(results.values()):
        print("\n✅ All providers are correctly installed and can be imported")
    else:
        print("\n❌ Some providers are not correctly installed or cannot be imported")
    
    return results

if __name__ == "__main__":
    check_providers()