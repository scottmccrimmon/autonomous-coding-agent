"""
Base class for all PAR harness skills.

New skills should inherit from BaseSkill and define a class-level `name`
attribute. Override `is_available()` to guard skills that require external
credentials or optional packages, and override `build()` if the constructor
itself reads environment variables or performs optional imports.

Skills that require constructor arguments (such as a working directory)
should not rely on `build()` and are instead instantiated directly in
`build_skill_registry()`.
"""

from abc import ABC


class BaseSkill(ABC):
    """
    Abstract base for all PAR harness skills.

    Subclasses must define:
        name (str): The key used to register and retrieve this skill from
                    the SkillRegistry.

    Subclasses may override:
        is_available(): Returns False to prevent registration when
                        prerequisites (env vars, packages) are missing.
        build():        Factory method for skills whose constructors read
                        environment variables or import optional packages.
    """

    name: str

    @classmethod
    def is_available(cls) -> bool:
        """
        Return True if this skill can be instantiated in the current environment.

        Override to check for required environment variables or optional package
        installations before the registry attempts to construct the skill.
        The default implementation always returns True.
        """
        return True

    @classmethod
    def build(cls) -> "BaseSkill":
        """
        Construct and return a skill instance.

        Override this method if the skill's constructor reads environment
        variables or imports optional packages that may not be present.
        The default implementation calls the constructor with no arguments.
        """
        return cls()
