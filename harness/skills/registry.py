"""
SkillRegistry and build_skill_registry for the PAR harness.

The registry provides a centralised store for harness-managed skills.
Skills are registered by name and invoked deterministically by the harness —
the LLM never decides when to call a skill. This keeps operations like pytest
runs and GitHub commits predictable and auditable regardless of agent output.
"""

from pathlib import Path
from typing import Dict, Type

from .base import BaseSkill
from .github import GitHubSkill
from .shell import ShellSkill


class SkillRegistry:
    """
    Centralised store for harness-managed skills.

    Skills are registered by name and retrieved by the harness at the point
    of use. The LLM never decides when to invoke a skill — all invocations
    are deterministic and controlled by the orchestration loop.
    """

    def __init__(self):
        """Initialise with an empty skills dictionary."""
        self._skills: Dict[str, BaseSkill] = {}

    def register(self, name: str, skill_instance: BaseSkill) -> None:
        """Register a skill instance under the given name."""
        self._skills[name] = skill_instance
        print(f"  [registry] Registered skill: {name}")

    def register_if_available(self, skill_cls: Type[BaseSkill]) -> None:
        """
        Check availability, build, and register a skill — or skip gracefully.

        Calls skill_cls.is_available() before attempting construction. If
        construction raises an exception, logs the error and continues rather
        than crashing the harness.

        Use this method for skills that depend on environment variables or
        optional packages. Skills that require constructor arguments (such as
        a working directory) should be instantiated and registered directly
        via register().
        """
        if not skill_cls.is_available():
            print(f"  [registry] {skill_cls.name} skipped (not available).")
            return

        try:
            self.register(skill_cls.name, skill_cls.build())
        except Exception as error:
            print(f"  [registry] {skill_cls.name} unavailable: {error}")

    def get(self, name: str) -> BaseSkill:
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


def build_skill_registry(output_root: Path) -> SkillRegistry:
    """
    Build and return the skill registry for this run.

    ShellSkill requires a working directory so is constructed and registered
    directly. GitHubSkill and any future credential-based skills use
    register_if_available(), which skips gracefully when prerequisites are
    absent — so the harness can run locally without GitHub credentials.

    To add a new skill:
        1. Implement it in a new file under harness/skills/, subclassing BaseSkill.
        2. Import it here.
        3. If it needs only env vars: add it to the register_if_available() calls.
           If it needs constructor args: instantiate it directly and call register().
    """
    registry = SkillRegistry()

    # ShellSkill requires a working directory — construct and register directly.
    registry.register(ShellSkill.name, ShellSkill(working_directory=output_root))

    # GitHubSkill — skip gracefully if credentials are absent.
    registry.register_if_available(GitHubSkill)

    return registry
