"""
Main entry point for CareSetu Voice Agent
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

# Import the main function from agent.py
from src.agent import main

if __name__ == "__main__":
    main()