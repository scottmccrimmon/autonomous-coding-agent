"""
harness/skills — skill implementations and registry for the PAR harness.

Public API:
    BaseSkill            — abstract base class; subclass to add new skills
    ShellSkill           — runs pytest, black, and syntax checks
    GitHubSkill          — creates repos and commits files via PyGithub
    SkillRegistry        — stores and retrieves registered skill instances
    build_skill_registry — constructs the standard registry for a run
"""

from .base import BaseSkill
from .github import GitHubSkill
from .registry import SkillRegistry, build_skill_registry
from .shell import ShellSkill

__all__ = [
    "BaseSkill",
    "GitHubSkill",
    "ShellSkill",
    "SkillRegistry",
    "build_skill_registry",
]
