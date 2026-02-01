import subprocess
import sys

def test_training_script_runs():
    # Intentionally blunt smoke test: ensure training runs without crashing and respects basic contracts.
    result = subprocess.run(
        [sys.executable, "src/train.py"],
        capture_output=True,
        text=True
    )

    assert result.returncode == 0
