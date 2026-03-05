"""
ShellSkill — executes shell commands in a controlled working directory.

Intended for pytest, black, and syntax checking only. All commands run with
a timeout to prevent runaway processes. stdout and stderr are captured and
returned as a single string for injection into agent prompts.

Note: ShellSkill does not implement build() because it requires a working
directory at construction time. It is instantiated directly in
build_skill_registry() rather than via the BaseSkill.build() factory.
"""

import subprocess
import sys
from pathlib import Path
from typing import List

from .base import BaseSkill


class ShellSkill(BaseSkill):
    """
    Executes shell commands in a controlled working directory.

    All commands are run with a timeout to prevent runaway processes.
    stdout and stderr are captured and returned as a single string,
    which is suitable for injection into agent prompts.
    """

    name = "shell"

    DEFAULT_TIMEOUT_SECONDS = 60

    def __init__(self, working_directory: Path):
        """
        Initialise the skill with a fixed working directory.

        All commands run by this skill will use working_directory as
        their current working directory.
        """
        self.working_directory = working_directory

    def run(self, command: List[str], timeout: int = DEFAULT_TIMEOUT_SECONDS) -> str:
        """
        Run a shell command and return combined stdout + stderr output.

        Args:
            command:  Command as a list of strings, e.g. ["pytest", "tests/"]
            timeout:  Maximum seconds to wait before killing the process.

        Returns:
            A single string combining stdout and stderr output.

        Raises:
            RuntimeError if the working directory does not exist.
        """
        if not self.working_directory.exists():
            raise RuntimeError(
                f"ShellSkill working directory does not exist: "
                f"{self.working_directory}"
            )

        print(f"  [shell] Running: {' '.join(command)}")

        result = subprocess.run(
            command,
            cwd=self.working_directory,
            capture_output=True,
            text=True,
            timeout=timeout,
        )

        combined_output = result.stdout + result.stderr
        print(combined_output)
        return combined_output

    def check_syntax(self) -> str:
        """
        Run py_compile against every .py file in the working directory.

        This catches syntax errors before pytest even attempts to collect
        tests — giving the Reflect agent precise line-level error messages
        rather than confusing collection failures.

        Returns a human-readable summary string. If all files pass,
        returns a brief success message. If any file fails, returns the
        compiler error details for each failing file.
        """
        python_files = list(Path(self.working_directory).rglob("*.py"))

        if not python_files:
            return "[syntax-check] No .py files found to check."

        errors = []
        for py_file in sorted(python_files):
            result = self.run(
                [sys.executable, "-m", "py_compile", str(py_file)]
            )
            if result.strip():
                relative_path = py_file.relative_to(self.working_directory)
                errors.append(f"{relative_path}: {result.strip()}")

        if errors:
            error_summary = "".join(errors)
            return f"[syntax-check] SYNTAX ERRORS FOUND:{error_summary}"

        return f"[syntax-check] All {len(python_files)} .py files passed syntax check."

    def run_pytest(self) -> str:
        """
        Run pytest against the tests/ directory.

        Uses sys.executable to invoke pytest as a module (-m pytest)
        rather than relying on a 'pytest' binary being on PATH. This
        ensures the correct virtualenv is always used, regardless of
        how the harness was launched.

        Returns the full pytest output as a string, which is injected
        into the Reflect prompt as {{PYTEST_RESULTS}}.
        """
        return self.run([sys.executable, "-m", "pytest", "tests/", "-v"])

    def run_black(self) -> str:
        """
        Run black formatter across the working directory.

        Uses sys.executable to invoke black as a module, consistent
        with run_pytest. Optional — call before pytest if you want
        consistent formatting in the committed output.
        """
        return self.run([sys.executable, "-m", "black", "."])
