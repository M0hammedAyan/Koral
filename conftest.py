import sys
import os

_root = os.path.dirname(__file__)

# Repo root — for backend package
sys.path.insert(0, _root)
# agents/ — for base_agent import in agent tests
sys.path.insert(0, os.path.join(_root, "agents"))
# Member 5 modules — for feedback/threshold imports in backend feedback route
sys.path.insert(0, os.path.join(_root, "SYSTEM INTELLIGENCE & EVALUATION"))
