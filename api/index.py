import sys
from pathlib import Path

# Add the backend directory to the Python path so imports work correctly
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import app  # Import the FastAPI app from main.py

# Vercel expects the application object to be named 'app'
# The application is already defined in main.py as a FastAPI instance
handler = app