"""
Supabase client configuration.
"""

import os
import sys
from pathlib import Path

# Try to import supabase
try:
    from supabase import create_client, Client
except ImportError:
    print("❌ Error: 'supabase' package not installed. Please run: pip install supabase")
    sys.exit(1)

# Try to import dotenv
try:
    from dotenv import load_dotenv
    # Load environment variables
    load_dotenv()
except ImportError:
    # dotenv not available, will use environment variables only
    pass

# Get Supabase credentials from environment
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("\n❌ Error: Supabase credentials not found!")
    print("\nPlease create a .env file with your Supabase credentials:")
    print("  SUPABASE_URL=your_supabase_url")
    print("  SUPABASE_KEY=your_supabase_key")
    print("\nOr set them as environment variables.")
    
    # Check if .env.example exists
    env_example = Path(__file__).parent / ".env.example"
    if env_example.exists():
        print(f"\n💡 You can copy .env.example to .env and fill in your credentials:")
        print(f"   cp .env.example .env")
    
    raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set")

# Create Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Export the client
__all__ = ['supabase']