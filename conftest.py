"""
Root-level conftest.py — ensures `backend/` is on sys.path.

This file is picked up by pytest regardless of the directory it is invoked
from (project root OR backend/).  It guarantees that `from app.xxx import ...`
works in every test without requiring the caller to cd into backend/ first.
"""

import os
import sys

# Absolute path to the backend/ directory
BACKEND_DIR = os.path.join(os.path.dirname(__file__), "backend")

if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)
