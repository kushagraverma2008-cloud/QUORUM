import os
import sys
from pathlib import Path

# Force offline mode for all tests
os.environ["GEMINI_API_KEY"] = ""
os.environ["APP_ENV"] = "test"
os.environ["DEBUG"] = "false"

# Add src to sys.path
root_dir = Path(__file__).resolve().parent.parent
src_dir = root_dir / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))
