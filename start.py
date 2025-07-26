#!/usr/bin/env python3
"""
Railway Entry Point - Forces Python execution
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import and run the Railway agent
from agent_railway import main

if __name__ == "__main__":
    main()