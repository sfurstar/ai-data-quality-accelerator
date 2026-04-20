"""
conftest.py — pytest configuration
Adds the project root to sys.path so `import engine` works
without needing `pip install -e .`
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
