"""
Filesystem utilities for the PAR harness.

Provides the output boundary layer between the agent and the local filesystem:
safe writes, recursive reads, and parsing of FILE: sentinel blocks from agent
responses. All write operations are constrained to a caller-supplied output
root directory — the agent cannot write outside it.
"""

from pathlib import Path
from typing import Dict, List, Tuple


def parse_files_from_response(response: str) -> List[Tuple[str, str]]:
    """
    Extract FILE: sentinel blocks from an agent Act response.

    Expected format in the response:
        FILE: path/to/file.py
        <file contents>
        FILE: path/to/another.py
        <file contents>

    Returns a list of (relative_path, content) tuples in the order they
    appear in the response.
    """
    files = []
    current_path = None
    current_lines = []

    for line in response.splitlines():
        if line.startswith("FILE:"):
            if current_path is not None:
                files.append((current_path, "\n".join(current_lines).rstrip()))
            current_path = line.replace("FILE:", "").strip()
            current_lines = []
        else:
            if current_path is not None:
                current_lines.append(line)

    # Capture the final file block
    if current_path is not None:
        files.append((current_path, "\n".join(current_lines).rstrip()))

    return files


def safe_write_file(output_root: Path, relative_path: str, content: str) -> None:
    """
    Write a file relative to output_root, enforcing a write boundary.

    Raises ValueError if the resolved path falls outside output_root.
    This prevents the agent from writing anywhere on the filesystem,
    regardless of what path string the agent produces.

    Args:
        output_root:   The root directory all writes must stay within.
        relative_path: Path relative to output_root for the file to write.
        content:       File contents to write.
    """
    target_path = (output_root / relative_path).resolve()
    output_root_resolved = output_root.resolve()

    if not str(target_path).startswith(str(output_root_resolved)):
        raise ValueError(
            f"Write boundary violation — refusing to write outside "
            f"{output_root_resolved}. Attempted path: {target_path}"
        )

    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(content)
    print(f"  [filesystem] Wrote: {relative_path}")


def read_generated_files(output_root: Path) -> Dict[str, str]:
    """
    Read back all source files the agent generated during the Act phase.

    Walks output_root recursively and returns a dict of
    {relative_path_string: file_content}. Used to inject the actual
    generated output into the Reflect prompt.

    Skips directories that contain runtime output (data, caches, venvs)
    to avoid injecting large data files or non-UTF-8 content into prompts.

    Args:
        output_root: The root directory to walk.

    Returns:
        Dict mapping relative path strings to file contents.
    """
    generated = {}

    if not output_root.exists():
        return generated

    # Directories that contain runtime output rather than generated source
    # files. Skip these to avoid injecting large data files or non-UTF-8
    # content into the Reflect prompt.
    skip_directories = {"data", ".venv", "__pycache__", ".pytest_cache", ".git"}

    for file_path in output_root.rglob("*"):
        if not file_path.is_file():
            continue

        # Skip any file whose path passes through a runtime-only directory
        relative_parts = file_path.relative_to(output_root).parts
        if any(part in skip_directories for part in relative_parts):
            continue

        relative_key = str(file_path.relative_to(output_root))

        try:
            generated[relative_key] = file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            # Skip binary files — they are not useful in the Reflect prompt
            print(f"  [filesystem] Skipping binary file: {relative_key}")

    return generated
