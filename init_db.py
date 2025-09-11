#!/usr/bin/env python3
"""
Database initialization script
"""

import sys
import os

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.app import create_app
from backend.models.models import init_db

if __name__ == '__main__':
    print("Initializing database...")
    app = create_app('development')
    with app.app_context():
        init_db()
    print("Database initialized successfully!")
