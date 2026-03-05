"""
Agent interaction layer for the PAR harness.

Handles all communication with the Claude API: loading and rendering prompt
templates, calling the Anthropic Messages API, and executing each phase of
the Plan-Act-Reflect loop. This module owns the LLM client, model config,
and all prompt I/O — loop.py calls into here without needing to know about
the underlying API.
"""

import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional

import anthropic

# ---------------------------------------------------------------------------
# Ensure the harness directory is on sys.path so sibling modules
# (filesystem) are importable regardless of how this module is loaded.
# ---------------------------------------------------------------------------

sys.path.insert(0, str(Path(__file__).resolve().parent))

from filesystem import parse_files_from_response, safe_write_file

# ---------------------------------------------------------------------------
# Path constants — derived from this file's location, not passed in.
# Prompt templates and agent documents live in agent/ at the project root.
# ---------------------------------------------------------------------------

_HARNESS_DIR = Path(__file__).resolve().parent
_AGENT_ROOT = _HARNESS_DIR.parent / "agent"

# ---------------------------------------------------------------------------
# Model configuration
# ---------------------------------------------------------------------------

MODEL = "claude-sonnet-4-5"
MAX_TOKENS_PLAN    = 8192   # Prose plan — generous but not excessive
MAX_TOKENS_ACT     = 16000  # 9 files of documented Python — needs real room
MAX_TOKENS_REFLECT = 1024   # JSON blob only — tiny

# ---------------------------------------------------------------------------
# Anthropic client — reads ANTHROPIC_API_KEY from environment
# ---------------------------------------------------------------------------

_client = anthropic.Anthropic()


# ---------------------------------------------------------------------------
# Prompt loading and rendering
# ---------------------------------------------------------------------------

def load_prompt(name: str) -> str:
    """
    Load a named prompt template from the agent/prompts/ directory.

    Args:
        name: Template name without extension, e.g. "plan", "act", "reflect".

    Returns:
        The raw template string with {{VARIABLE}} placeholders intact.
    """
    prompt_path = _AGENT_ROOT / "prompts" / f"{name}.md"
    return prompt_path.read_text()


def render_prompt(template: str, variables: Dict[str, str]) -> str:
    """
    Replace {{VARIABLE}} placeholders in a template string.

    Each key in variables replaces its corresponding {{KEY}} marker.
    Keys are case-sensitive and must match the template exactly.

    Args:
        template:  Template string containing {{VARIABLE}} markers.
        variables: Dict mapping marker names to replacement values.

    Returns:
        The rendered string with all placeholders replaced.
    """
    rendered = template
    for key, value in variables.items():
        rendered = rendered.replace(f"{{{{{key}}}}}", value)
    return rendered


# ---------------------------------------------------------------------------
# Agent context loading
# ---------------------------------------------------------------------------

def load_agent_context() -> Dict[str, str]:
    """
    Load the fixed documents the agent needs across all loop phases.

    Returns a dict with keys matching the filenames, e.g.:
        context["task_spec.md"]
        context["acceptance_criteria.md"]
        context["reflection_rubric.md"]
    """
    context = {}
    documents = [
        "task_spec.md",
        "acceptance_criteria.md",
        "reflection_rubric.md",
    ]
    for filename in documents:
        file_path = _AGENT_ROOT / filename
        context[filename] = file_path.read_text()
    return context


# ---------------------------------------------------------------------------
# LLM call — Anthropic Messages API
# ---------------------------------------------------------------------------

def call_llm(
    prompt: str,
    max_tokens: int = MAX_TOKENS_ACT,
    system: Optional[str] = None,
) -> str:
    """
    Send a prompt to Claude and return the text response.

    Uses the Anthropic Messages API (client.messages.create).
    The response text is at response.content[0].text.

    Args:
        prompt:     The user message to send.
        max_tokens: Maximum tokens in the response.
        system:     Optional system prompt string.

    Returns:
        The model's text response.
    """
    messages = [{"role": "user", "content": prompt}]

    call_kwargs = {
        "model": MODEL,
        "max_tokens": max_tokens,
        "messages": messages,
    }
    if system:
        call_kwargs["system"] = system

    response = _client.messages.create(**call_kwargs)
    return response.content[0].text


# ---------------------------------------------------------------------------
# PAR Phase: Plan
# ---------------------------------------------------------------------------

def agent_plan(context: Dict[str, str]) -> str:
    """
    Run the Plan phase: ask the agent to produce a concrete implementation plan.

    Injects the task specification into the plan prompt template.
    Returns the plan text, which is passed to the Act phase.

    Args:
        context: Agent context dict containing "task_spec.md" and other docs.

    Returns:
        The plan text produced by the model.
    """
    template = load_prompt("plan")
    prompt = render_prompt(
        template,
        {"TASK_SPEC": context["task_spec.md"]},
    )

    print("\n--- PLAN ---")
    plan = call_llm(prompt, max_tokens=MAX_TOKENS_PLAN)
    print(plan)
    return plan


# ---------------------------------------------------------------------------
# PAR Phase: Act
# ---------------------------------------------------------------------------

def agent_act(
    plan: str,
    output_root: Path,
    prior_issues: Optional[List[str]] = None,
) -> None:
    """
    Run the Act phase: ask the agent to implement the plan and write files.

    Parses FILE: sentinel blocks from the model response and writes each
    file to output_root via safe_write_file. On retry iterations, the
    prior_issues list is appended to the prompt so the agent knows what
    to fix.

    Args:
        plan:         The implementation plan from the Plan phase.
        output_root:  Root directory where generated files are written.
        prior_issues: Issues from the previous Reflect phase, if any.
    """
    template = load_prompt("act")
    prompt = render_prompt(template, {"PLAN": plan})

    # On retry iterations, append the specific issues to fix
    if prior_issues:
        issues_text = "\n".join(f"- {issue}" for issue in prior_issues)
        prompt += (
            f"\n\n---\n\n"
            f"## CRITICAL: Fixes Required From Previous Attempt\n\n"
            f"The previous implementation failed. You MUST fix ALL of the "
            f"following issues before producing any FILE blocks. Do not "
            f"regenerate working files unchanged — focus your changes on "
            f"the failing code:\n\n{issues_text}"
        )

    print("\n--- ACT ---")
    response = call_llm(prompt, max_tokens=MAX_TOKENS_ACT)
    print(response)

    files = parse_files_from_response(response)
    if not files:
        raise RuntimeError(
            "Agent Act response contained no FILE: blocks. "
            "The response may be malformed or the agent may have "
            "refused to produce output."
        )

    for relative_path, content in files:
        safe_write_file(output_root, relative_path, content)


# ---------------------------------------------------------------------------
# PAR Phase: Reflect
# ---------------------------------------------------------------------------

def agent_reflect(
    context: Dict[str, str],
    generated_files: Dict[str, str],
    pytest_results: str,
) -> dict:
    """
    Run the Reflect phase: ask the agent to evaluate its own output.

    Injects the actual generated files and pytest results into the prompt
    so the agent evaluates real artifacts, not its intentions. Returns
    a parsed reflection dict with keys: scores, acceptance_met, issues,
    confidence, done.

    Args:
        context:         Agent context dict containing "acceptance_criteria.md".
        generated_files: Dict of {relative_path: content} from the Act phase.
        pytest_results:  Combined syntax check and pytest output string.

    Returns:
        Parsed reflection dict from the model.
    """
    template = load_prompt("reflect")

    # Format the generated files as a readable block for prompt injection
    files_block = "\n\n".join(
        f"FILE: {path}\n{content}"
        for path, content in generated_files.items()
    )

    prompt = render_prompt(
        template,
        {
            "GENERATED_FILES": files_block,
            "PYTEST_RESULTS": pytest_results,
            "ACCEPTANCE_CRITERIA": context["acceptance_criteria.md"],
        },
    )

    print("\n--- REFLECT ---")
    response = call_llm(prompt, max_tokens=MAX_TOKENS_REFLECT)
    print(response)

    # Strip markdown code fences if the model wraps its JSON output
    clean_response = response.strip()
    if clean_response.startswith("```"):
        clean_response = re.sub(r"^```[a-z]*\n?", "", clean_response)
        clean_response = re.sub(r"\n?```$", "", clean_response)

    try:
        reflection = json.loads(clean_response)
    except json.JSONDecodeError as parse_error:
        raise RuntimeError(
            f"Reflect phase returned invalid JSON.\n"
            f"Raw response:\n{response}"
        ) from parse_error

    required_keys = {"scores", "acceptance_met", "issues", "confidence", "done"}
    missing_keys = required_keys - reflection.keys()
    if missing_keys:
        raise RuntimeError(
            f"Reflect phase JSON is missing required keys: {missing_keys}"
        )

    return reflection


# ---------------------------------------------------------------------------
# Completion check
# ---------------------------------------------------------------------------

def is_done(reflection: dict, iteration: int) -> bool:
    """
    Determine whether the PAR loop should stop after this iteration.

    Returns True only when the agent's reflection says done=True.
    Handles non-boolean done values defensively rather than crashing.

    Args:
        reflection: The parsed reflection dict from agent_reflect.
        iteration:  Current iteration index (used for logging context).

    Returns:
        True if the loop should stop, False if it should continue.
    """
    done_value = reflection.get("done", False)

    if not isinstance(done_value, bool):
        print(
            f"  Warning: reflection['done'] has unexpected type "
            f"{type(done_value).__name__} with value {done_value!r}. "
            f"Treating as False."
        )
        return False

    return done_value
