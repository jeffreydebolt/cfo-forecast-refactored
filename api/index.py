from fastapi import FastAPI
from mangum import Mangum
import sys
import os

# Add current directory to Python path
sys.path.append(os.path.dirname(__file__))

from simplified_main import app

# Create handler for Vercel
handler = Mangum(app)