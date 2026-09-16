from dataclasses import asdict

from ..errors import NotFoundError
from ..models import Issue, Repository
from .base import Service


class GitHub(Service):
    name = "github"

    def __init__(self):
        self.repositories: dict[str, Repository] = {}
        self.issues: dict[str, Issue] = {}

    def create_repository(self, *, owner: str, name: str, description: str = "") -> Repository:
        self._before("create_repository")
        repository = Repository(self.ids.new("repo"), owner, name, description, ())
        self.repositories[repository.id] = repository
        self.events.emit("github.repository.created", {"repository_id": repository.id})
        return repository

    def _repo(self, owner: str, repo: str) -> Repository:
        for item in self.repositories.values():
            if item.owner == owner and item.name == repo:
                return item
        raise NotFoundError(f"repository {owner}/{repo} does not exist")

    def create_issue(self, *, owner: str, repo: str, title: str, body: str = "") -> Issue:
        self._before("create_issue")
        repository = self._repo(owner, repo)
        number = len(repository.issue_ids) + 1
        issue = Issue(self.ids.new("issue"), number, owner, repo, title, body, "open", self.events.clock.now().isoformat())
        self.issues[issue.id] = issue
        self.repositories[repository.id] = Repository(repository.id, repository.owner, repository.name, repository.description, (*repository.issue_ids, issue.id))
        self.events.emit("github.issue.created", {"issue_id": issue.id, "owner": owner, "repo": repo})
        return issue

    def list_issues(self, *, owner: str, repo: str, state: str = "open") -> list[Issue]:
        repository = self._repo(owner, repo)
        return [self.issues[item_id] for item_id in repository.issue_ids if state == "all" or self.issues[item_id].state == state]

    def close_issue(self, *, owner: str, repo: str, number: int) -> Issue:
        issue = next((item for item in self.list_issues(owner=owner, repo=repo, state="all") if item.number == number), None)
        if issue is None:
            raise NotFoundError(f"issue {owner}/{repo}#{number} does not exist")
        updated = Issue(issue.id, issue.number, issue.owner, issue.repo, issue.title, issue.body, "closed", issue.created_at)
        self.issues[issue.id] = updated
        self.events.emit("github.issue.closed", {"issue_id": issue.id})
        return updated

    def snapshot_state(self):
        return {"repositories": {key: asdict(value) for key, value in self.repositories.items()}, "issues": {key: asdict(value) for key, value in self.issues.items()}}

    def restore_state(self, data):
        self.repositories = {key: Repository(**value) for key, value in data.get("repositories", {}).items()}
        self.issues = {key: Issue(**value) for key, value in data.get("issues", {}).items()}
