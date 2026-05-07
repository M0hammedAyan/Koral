import sys
import os

_root = os.path.dirname(os.path.abspath(__file__))

# Repo root — makes `backend`, `feedback`, `threshold` importable as packages
sys.path.insert(0, _root)

# agents/ — makes `base_agent` importable directly
sys.path.insert(0, os.path.join(_root, "agents"))

# system-intelligence-evaluation — makes `feedback`, `threshold` importable
# (backend/routes/feedback.py does: from feedback.feedback_loop import process_feedback)
sys.path.insert(0, os.path.join(_root, "system-intelligence-evaluation"))
