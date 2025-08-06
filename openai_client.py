"""
OpenAI client configuration.
"""

import os
import sys

# Try to import openai
try:
    from openai import OpenAI
except ImportError:
    print("❌ Error: 'openai' package not installed. Please run: pip install openai")
    sys.exit(1)

# Try to import dotenv
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Get OpenAI API key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    print("\n⚠️  Warning: OpenAI API key not found!")
    print("AI features will be disabled.")
    print("\nTo enable AI features, add to your .env file:")
    print("  OPENAI_API_KEY=sk-your-api-key")
    openai_client = None
else:
    # Create OpenAI client
    openai_client = OpenAI(api_key=OPENAI_API_KEY)

# Export
__all__ = ['openai_client']