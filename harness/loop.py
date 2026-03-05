# harness/loop.py
#
# PAR Loop Harness - Phase 2
#
# Orchestrates the Plan-Act-Reflect loop for autonomous code generation.
# Migrated from OpenAI Responses API to Anthropic Messages API.
# Adds ShellSkill (pytest execution) and GitHubSkill (repo + commit).
#
# Dependencies:
#   pip install anthropic PyGithub
#
# Required environment variables:
#   ANTHROPIC_API_KEY   — Anthropic API access
#   GITHUB_PAT          — GitHub personal access token (for GitHubSkill)
#   GITHUB_USERNAME     — GitHub username (for GitHubSkill)

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, Optional

import anthropic

# ---------------------------------------------------------------------------
# Path constants — must match the actual repo layout exactly
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]
AGENT_ROOT = PROJECT_ROOT / "agent"
OUTPUT_ROOT = PROJECT_ROOT / "fhir-patient-analysis"

# ---------------------------------------------------------------------------
# Model configuration
# ---------------------------------------------------------------------------

MODEL = "claude-sonnet-4-5"
MAX_TOKENS_PLAN    = 8192   # Prose plan — generous but not excessive
MAX_TOKENS_ACT     = 16000  # 9 files of documented Python — needs real room
MAX_TOKENS_REFLECT = 1024   # JSON blob only — tiny

# ---------------------------------------------------------------------------
# Anthropic client
# ---------------------------------------------------------------------------

client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from environment


# ---------------------------------------------------------------------------
# Prompt loading and rendering
# ---------------------------------------------------------------------------

def load_prompt(name: str) -> str:
    """Load a named prompt template from agent/prompts/."""
    prompt_path = AGENT_ROOT / "prompts" / f"{name}.md"
    return prompt_path.read_text()


def render_prompt(template: str, variables: dict) -> str:
    """
    Replace {{VARIABLE}} placeholders in a template string.

    Each key in variables replaces its corresponding {{KEY}} marker.
    Keys are case-sensitive and must match the template exactly.
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
        file_path = AGENT_ROOT / filename
        context[filename] = file_path.read_text()
    return context


# ---------------------------------------------------------------------------
# Safe filesystem writes — enforces output boundary
# ---------------------------------------------------------------------------

def safe_write_file(relative_path: str, content: str) -> None:
    """
    Write a file relative to OUTPUT_ROOT, enforcing write boundaries.

    Raises ValueError if the resolved path falls outside OUTPUT_ROOT.
    This prevents the agent from writing anywhere on the filesystem.
    """
    target_path = (OUTPUT_ROOT / relative_path).resolve()
    output_root_resolved = OUTPUT_ROOT.resolve()

    if not str(target_path).startswith(str(output_root_resolved)):
        raise ValueError(
            f"Write boundary violation — refusing to write outside "
            f"{output_root_resolved}. Attempted path: {target_path}"
        )

    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(content)
    print(f"  [filesystem] Wrote: {relative_path}")


def read_generated_files() -> Dict[str, str]:
    """
    Read back all files the agent generated during the Act phase.

    Walks OUTPUT_ROOT recursively and returns a dict of
    {relative_path_string: file_content}. Used to inject the actual
    generated output into the Reflect prompt.
    """
    generated = {}

    if not OUTPUT_ROOT.exists():
        return generated

    # Directories that contain runtime output rather than generated source
    # files. We skip these to avoid injecting large data files or non-UTF-8
    # content into the Reflect prompt.
    skip_directories = {"data", ".venv", "__pycache__", ".pytest_cache", ".git"}

    for file_path in OUTPUT_ROOT.rglob("*"):
        if not file_path.is_file():
            continue

        # Skip any file whose path passes through a runtime-only directory
        relative_parts = file_path.relative_to(OUTPUT_ROOT).parts
        if any(part in skip_directories for part in relative_parts):
            continue

        relative_key = str(file_path.relative_to(OUTPUT_ROOT))

        try:
            generated[relative_key] = file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            # Skip binary files — they are not useful in the Reflect prompt
            print(f"  [read_files] Skipping binary file: {relative_key}")

    return generated


# ---------------------------------------------------------------------------
# Agent response parsing
# ---------------------------------------------------------------------------

def parse_files_from_response(response: str) -> list:
    """
    Extract FILE: sentinel blocks from the agent Act response.

    Expected format in the response:
        FILE: path/to/file.py
        <file contents>
        FILE: path/to/another.py
        <file contents>

    Returns a list of (relative_path, content) tuples.
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


# ---------------------------------------------------------------------------
# LLM call — Anthropic Messages API
# ---------------------------------------------------------------------------

def call_llm(prompt: str, max_tokens: int = MAX_TOKENS_ACT, system: Optional[str] = None) -> str:
    """
    Send a prompt to Claude and return the text response.

    Uses the Anthropic Messages API (client.messages.create).
    The response text is at response.content[0].text — note this differs
    from the OpenAI Responses API which used response.output_text.
    """
    messages = [{"role": "user", "content": prompt}]

    call_kwargs = {
        "model": MODEL,
        "max_tokens": max_tokens,
        "messages": messages,
    }
    if system:
        call_kwargs["system"] = system

    response = client.messages.create(**call_kwargs)
    return response.content[0].text


# ---------------------------------------------------------------------------
# PAR Phase: Plan
# ---------------------------------------------------------------------------

def agent_plan(context: Dict[str, str]) -> str:
    """
    Run the Plan phase: ask the agent to produce a concrete implementation plan.

    Injects the task specification into the plan prompt template.
    Returns the plan text, which is passed to the Act phase.
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

def agent_act(plan: str, prior_issues: list = None) -> None:
    """
    Run the Act phase: ask the agent to implement the plan and write files.
    ...
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
        safe_write_file(relative_path, content)


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
# Skill: Shell execution
# ---------------------------------------------------------------------------

class ShellSkill:
    """
    Executes shell commands in a controlled working directory.

    Intended for pytest and black only — not for git operations.
    All commands are run with a timeout to prevent runaway processes.
    stdout and stderr are captured and returned as a single string.
    """

    DEFAULT_TIMEOUT_SECONDS = 60

    def __init__(self, working_directory: Path):
        """
        Initialise the skill with a fixed working directory.

        All commands run by this skill will use working_directory as
        their current working directory.
        """
        self.working_directory = working_directory

    def run(self, command: list, timeout: int = DEFAULT_TIMEOUT_SECONDS) -> str:
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
        Run py_compile against every .py file in the project root.

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
        Run black formatter across the project root.

        Uses sys.executable to invoke black as a module, consistent
        with run_pytest. Optional — call before pytest if you want
        consistent formatting in the committed output.
        """
        return self.run([sys.executable, "-m", "black", "."])


# ---------------------------------------------------------------------------
# Skill: GitHub repository management
# ---------------------------------------------------------------------------

class GitHubSkill:
    """
    Creates GitHub repositories and commits files via the PyGithub API.

    Design philosophy: linear commits only — no branches, no PRs, no
    merge conflicts. The agent is the sole writer; the commit history
    is a clean, auditable trail of what was generated and when.

    Requires:
        pip install PyGithub
        Environment variables: GITHUB_PAT, GITHUB_USERNAME
    """

    def __init__(self):
        """
        Initialise the GitHub client from environment variables.

        Raises ImportError if PyGithub is not installed.
        Raises EnvironmentError if required env vars are missing.
        """
        try:
            from github import Github, GithubException
            self._GithubException = GithubException
        except ImportError:
            raise ImportError(
                "PyGithub is required for GitHubSkill. "
                "Install it with: pip install PyGithub"
            )

        token = os.environ.get("GITHUB_PAT")
        username = os.environ.get("GITHUB_USERNAME")

        if not token or not username:
            raise EnvironmentError(
                "GITHUB_PAT and GITHUB_USERNAME environment variables "
                "are required for GitHubSkill."
            )

        from github import Github
        self.client = Github(token)
        self.user = self.client.get_user()

    def create_repo(
        self,
        name: str,
        description: str = "",
        private: bool = False,
    ):
        """
        Create a new GitHub repository.

        If the repository already exists, fetches and returns it instead
        of raising an error. This makes the operation safe to retry.
        """
        try:
            repo = self.user.create_repo(
                name=name,
                description=description,
                private=private,
                auto_init=True,  # creates main branch with an initial commit
            )
            print(f"  [github] Created repository: {repo.html_url}")
            return repo
        except self._GithubException as error:
            if error.status == 422:
                print(f"  [github] Repository '{name}' already exists — fetching.")
                return self.user.get_repo(name)
            raise

    def commit_files(
        self,
        repo_name: str,
        files: Dict[str, str],
        commit_message: str,
        branch: str = "main",
    ) -> None:
        """
        Commit a set of files to the repository's main branch.

        Args:
            repo_name:      Name of the repository (not the full URL).
            files:          Dict of {file_path: file_content} to commit.
            commit_message: Git commit message.
            branch:         Target branch — defaults to main.

        For each file, uses update_file if it already exists (requiring
        the current SHA), or create_file if it is new. Always targets
        the main branch — no branching strategy is used.
        """
        repo = self.user.get_repo(repo_name)

        for file_path, content in files.items():
            try:
                existing_file = repo.get_contents(file_path, ref=branch)
                repo.update_file(
                    path=file_path,
                    message=commit_message,
                    content=content,
                    sha=existing_file.sha,
                    branch=branch,
                )
                print(f"  [github] Updated: {file_path}")
            except self._GithubException as error:
                if error.status == 404:
                    repo.create_file(
                        path=file_path,
                        message=commit_message,
                        content=content,
                        branch=branch,
                    )
                    print(f"  [github] Created: {file_path}")
                else:
                    raise


# ---------------------------------------------------------------------------
# Skill registry
# ---------------------------------------------------------------------------

class SkillRegistry:
    """
    Lightweight registry for harness-managed skills.

    Skills are registered by name and called deterministically by the
    harness — the LLM never decides when to invoke a skill. This keeps
    operations like pytest runs and GitHub commits predictable and
    auditable regardless of what the agent produces.
    """

    def __init__(self):
        """Initialise with an empty skills dictionary."""
        self._skills = {}

    def register(self, name: str, skill_instance) -> None:
        """Register a skill under the given name."""
        self._skills[name] = skill_instance
        print(f"  [registry] Registered skill: {name}")

    def get(self, name: str):
        """
        Retrieve a registered skill by name.

        Raises KeyError if the skill has not been registered.
        """
        if name not in self._skills:
            raise KeyError(
                f"Skill '{name}' is not registered. "
                f"Available skills: {list(self._skills.keys())}"
            )
        return self._skills[name]

    @property
    def available(self) -> list:
        """Return a list of all registered skill names."""
        return list(self._skills.keys())


# ---------------------------------------------------------------------------
# Skill registry initialisation
# ---------------------------------------------------------------------------

def build_skill_registry() -> SkillRegistry:
    """
    Build and return the skill registry for this run.

    Skills that lack required environment variables are skipped
    gracefully so the harness can run without GitHub credentials
    when needed (e.g. local development and testing).
    """
    registry = SkillRegistry()

    # ShellSkill is always available — it has no external dependencies
    shell_skill = ShellSkill(working_directory=OUTPUT_ROOT)
    registry.register("shell", shell_skill)

    # GitHubSkill requires credentials — skip gracefully if absent
    github_pat = os.environ.get("GITHUB_PAT")
    github_username = os.environ.get("GITHUB_USERNAME")

    if github_pat and github_username:
        try:
            registry.register("github", GitHubSkill())
        except Exception as error:
            print(f"  [registry] GitHub skill unavailable: {error}")
    else:
        print(
            "  [registry] GitHub skill skipped "
            "(GITHUB_PAT or GITHUB_USERNAME not set)."
        )

    return registry


# ---------------------------------------------------------------------------
# Completion check
# ---------------------------------------------------------------------------

def is_done(reflection: dict, iteration: int) -> bool:
    """
    Determine whether the PAR loop should stop after this iteration.

    Returns True only when the agent's reflection says done AND no
    pytest failures are detected in the scores. Handles non-boolean
    done values defensively.
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


# ---------------------------------------------------------------------------
# Main PAR loop
# ---------------------------------------------------------------------------

def run_loop(
    max_iterations: int = 5,
    output_repo: Optional[str] = None,
    output_repo_description: str = "Generated by PAR loop autonomous coding agent",
    run_black_formatting: bool = False,
):
    """
    Run the Plan-Act-Reflect loop.

    Each iteration:
      1. Plan  — agent produces an implementation plan
      2. Act   — agent writes files to OUTPUT_ROOT
      3. Test  — harness runs pytest and captures output
      4. Reflect — agent evaluates its output against criteria
      5. Commit — harness commits files to GitHub (if enabled)

    The loop exits when the agent's reflection returns done=True,
    or when max_iterations is reached.

    Args:
        max_iterations:          Hard ceiling on loop iterations.
        output_repo:             GitHub repository name for committing
                                 generated files. Pass None to skip GitHub.
        output_repo_description: Description used when creating the repo.
        run_black_formatting:    If True, runs black before pytest each
                                 iteration. Optional quality-of-life step.
    """
    print("\n" + "=" * 60)
    print("  PAR Loop Starting")
    print("=" * 60)

    registry = build_skill_registry()
    shell = registry.get("shell")
    github_enabled = "github" in registry.available

    # Create the output repository once before the loop begins
    if output_repo and github_enabled:
        registry.get("github").create_repo(output_repo, output_repo_description)

    context = load_agent_context()

    prior_issues = []  # empty on first iteration

    for iteration in range(max_iterations):
        print(f"\n{'=' * 60}")
        print(f"  Iteration {iteration + 1} of {max_iterations}")
        print(f"{'=' * 60}")

        # --- Phase 1: Plan ---
        plan = agent_plan(context)

        # --- Phase 2: Act ---
        agent_act(plan, prior_issues=prior_issues)

        # --- Phase 3: Test (harness-driven, not agent-driven) ---
        if run_black_formatting:
            print("\n--- FORMAT (black) ---")
            shell.run_black()

        print("\n--- SYNTAX CHECK ---")
        syntax_output = shell.check_syntax()
        print(syntax_output)

        print("\n--- TEST (pytest) ---")
        pytest_output = shell.run_pytest()

        # Prepend syntax check results so the Reflect agent sees both.
        # If there are syntax errors, pytest collection will fail anyway;
        # the compiler output gives the agent precise line numbers.
        combined_test_output = syntax_output + "\n\n" + pytest_output

        # --- Phase 4: Reflect ---
        generated_files = read_generated_files()
        reflection = agent_reflect(context, generated_files, combined_test_output)

        prior_issues = reflection.get("issues", [])
        print("\n--- REFLECTION SUMMARY ---")
        print(json.dumps(reflection, indent=2))

        # --- Phase 5: Commit (harness-driven, only on success) ---
        task_is_done = is_done(reflection, iteration)

        if task_is_done and output_repo and github_enabled and generated_files:
            commit_message = (
                f"feat: initial FHIR patient data loader and analyzer"
            )
            registry.get("github").commit_files(
                repo_name=output_repo,
                files=generated_files,
                commit_message=commit_message,
            )

        # --- Loop control ---
        if task_is_done:
            print("\n✓ Agent reports task complete.")
            break
        else:
            issues = reflection.get("issues", [])
            if issues:
                print("\n  Issues to address in next iteration:")
                for issue in issues:
                    print(f"    - {issue}")
            print("\n↻ Continuing to next iteration.")

    else:
        print("\n⚠  Max iterations reached without completion.")

    print("\n" + "=" * 60)
    print("  PAR Loop Complete")
    print("=" * 60 + "\n")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    run_loop(
        max_iterations=5,
        output_repo=None,           # e.g. "fhir-patient-analysis"
        run_black_formatting=False,
    )
