"""
GitHubSkill — creates GitHub repositories and commits files via PyGithub.

Requires the GITHUB_PAT and GITHUB_USERNAME environment variables and the
PyGithub package (pip install PyGithub). The skill checks for both
prerequisites in is_available() so the registry can skip it gracefully
when credentials are absent.
"""

import os
from typing import Dict

from .base import BaseSkill


class GitHubSkill(BaseSkill):
    """
    Creates GitHub repositories and commits files via the PyGithub API.

    Design philosophy: linear commits only — no branches, no PRs, no
    merge conflicts. The agent is the sole writer; the commit history
    is a clean, auditable trail of what was generated and when.

    Requires:
        pip install PyGithub
        Environment variables: GITHUB_PAT, GITHUB_USERNAME
    """

    name = "github"

    @classmethod
    def is_available(cls) -> bool:
        """
        Return True if the required GitHub credentials are present.

        Checks for GITHUB_PAT and GITHUB_USERNAME environment variables
        without attempting to connect to GitHub or import PyGithub.
        """
        return bool(
            os.environ.get("GITHUB_PAT") and os.environ.get("GITHUB_USERNAME")
        )

    @classmethod
    def build(cls) -> "GitHubSkill":
        """
        Construct and return a GitHubSkill instance.

        Separates availability checking (is_available) from construction so
        that SkillRegistry can catch import and initialisation errors without
        a try/except at every call site.
        """
        return cls()

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
