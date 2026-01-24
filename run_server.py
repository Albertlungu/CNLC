#!/usr/bin/env python3
"""
Run script for the Flask API server.
Ensures the project root is in the Python path.
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Now import and run the server
from backend.api.server import app

if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5001)
