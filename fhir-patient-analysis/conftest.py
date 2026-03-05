
"""
pytest configuration file

This file ensures pytest can import project modules regardless of the
working directory from which tests are invoked.
"""

import sys
from pathlib import Path

# Add the project root to sys.path so pytest can find fhir_loader
# and fhir_analyzer when running tests from any working directory.
sys.path.insert(0, str(Path(__file__).parent))