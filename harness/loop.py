# harness/loop.py

from openai import OpenAI
from pathlib import Path
from typing import Dict
import re
import json

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MNIST_ROOT = PROJECT_ROOT / "mnist-cnn"
AGENT_ROOT = PROJECT_ROOT / "agent"

client = OpenAI()

def load_prompt(name: str) -> str:
    """Load a prompt template from agent/prompts."""
    path = AGENT_ROOT / "prompts" / f"{name}.md"
    return path.read_text()


def render_prompt(template: str, variables: dict) -> str:
    """Simple template renderer using {{VAR}} replacement."""
    rendered = template
    for key, value in variables.items():
        rendered = rendered.replace(f"{{{{{key}}}}}", value)
    return rendered

def load_context() -> Dict[str, str]:
    """Load task spec, acceptance criteria, and rubric."""
    context = {}
    for name in [
        "task_spec.md",
        "acceptance_criteria.md",
        "reflection_rubric.md",
    ]:
        path = AGENT_ROOT / name
        context[name] = path.read_text()
    return context


def read_project_tree() -> str:
    """Return a textual representation of the mnist-cnn directory tree."""
    lines = []
    for path in MNIST_ROOT.rglob("*"):
        if path.is_file():
            lines.append(str(path.relative_to(MNIST_ROOT)))
    return "\n".join(sorted(lines))

def safe_write_file(relative_path: str, content: str) -> None:
    """
    Write a file relative to the mnist-cnn root, enforcing safety constraints.
    """
    target_path = (MNIST_ROOT / relative_path).resolve()

    # Enforce write boundaries
    allowed_dirs = [
        (MNIST_ROOT / "docker").resolve(),
        (MNIST_ROOT / "README.md").resolve(),
    ]

    if not any(str(target_path).startswith(str(allowed)) for allowed in allowed_dirs):
        raise ValueError(f"Refusing to write outside allowed paths: {target_path}")

    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(content)

    print(f"[agent_act] Wrote {relative_path}")

def parse_files_from_response(response: str):
    files = []
    current_path = None
    current_lines = []

    for line in response.splitlines():
        if line.startswith("FILE:"):
            # Save previous file if exists
            if current_path is not None:
                files.append((current_path, "\n".join(current_lines).rstrip()))
            # Start new file
            current_path = line.replace("FILE:", "").strip()
            current_lines = []
        else:
            if current_path is not None:
                current_lines.append(line)

    # Save last file
    if current_path is not None:
        files.append((current_path, "\n".join(current_lines).rstrip()))

    return files

def agent_plan(context: Dict[str, str], project_tree: str) -> str:
    template = load_prompt("plan")

    prompt = render_prompt(
        template,
        {
            "TASK_SPEC": context["task_spec.md"],
            "PROJECT_TREE": project_tree,
        },
    )

    plan = call_llm(prompt)

    print("\n--- AGENT PLAN ---\n")
    print(plan)
    return plan

def agent_act(plan: str) -> None:
    template = load_prompt("act")

    prompt = render_prompt(
        template,
        {
            "PLAN": plan,
        },
    )

    response = call_llm(prompt)

    print("\n--- AGENT ACT RESPONSE ---\n")
    print(response)

    # Parse file blocks
    files = parse_files_from_response(response)

    if not files:
        raise RuntimeError("No files found in agent response.")

    for relative_path, content in files:
        safe_write_file(relative_path, content)

def agent_reflect(context: dict) -> dict:
    template = load_prompt("reflect")

    prompt = render_prompt(
        template,
        {
            "ACCEPTANCE_CRITERIA": context["acceptance_criteria.md"],
            "REFLECTION_RUBRIC": context["reflection_rubric.md"],
        },
    )

    response = call_llm(prompt)

    print("\n--- AGENT REFLECTION RESPONSE ---\n")
    print(response)

    try:
        reflection = json.loads(response)
    except json.JSONDecodeError as e:
        raise RuntimeError(
            "Reflection output was not valid JSON. "
            "Reflection prompt requires strict JSON output."
        ) from e

    required_keys = {
        "scores",
        "acceptance_met",
        "issues",
        "confidence",
        "done",
    }

    missing = required_keys - reflection.keys()
    if missing:
        raise RuntimeError(f"Reflection output missing keys: {missing}")

    return reflection


def call_llm(prompt: str) -> str:
    response = client.responses.create(
        model="gpt-4.1",
        input=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        max_output_tokens=800,
    )

    # Extract plain text output
    return response.output_text

def run_loop(max_iterations: int = 5):
    # Load the fixed inputs the agent will use each iteration.
    context = load_context()
    # Snapshot the project layout once to keep prompts consistent.
    project_tree = read_project_tree()

    for iteration in range(max_iterations):
        # Ask the model to propose a plan from the current context.
        plan = agent_plan(context, project_tree)
        # Execute the plan and apply any file changes it returns.
        agent_act(plan)
        # Judge the result against acceptance criteria and rubric.
        reflection = agent_reflect(context)

        # Report the reflection payload for transparency.
        print("\n--- REFLECTION SUMMARY ---")
        print(json.dumps(reflection, indent=2))

        # Exit early if the reflection says the task is complete.
        done = reflection.get("done", False)
        if not isinstance(done, bool):
            print(f'Warning: reflection["done"] is not boolean: {done!r}. Treating as False.')
            done = False

        if done:
            print("\nAgent reports task complete.")
            break
        else:
            # Continue to the next iteration when improvements are needed.
            print("\nAgent indicates further improvement needed. Continuing loop.")
    else:
        # Only runs if the loop ends without an early break.
        print("Max iterations reached without completion.")


if __name__ == "__main__":
    run_loop()
