"""
WSGI entrypoint for StealthHub Production
"""
import os
import sys

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app_railway import app

# Create the WSGI application
application = app

if __name__ == "__main__":
    application.run()
