import json
import sys
from pathlib import Path

import pytest

PROJECT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT))

from specbridge.agent.limits import Settings  # noqa: E402
from specbridge.agent.nodes import intake  # noqa: E402
from specbridge.atlassian import JiraError  # noqa: E402

FAKE_KEY = "sk-or-v1-TESTKEY-must-never-appear"
FAKE_JIRA_TOKEN = "jira-token-must-never-appear"
FIXTURES = Path(__file__).parent / "fixtures" / "jira"
JIRA_ENV = {"ATLASSIAN_SITE": "https://rooks101.atlassian.net", "ATLASSIAN_EMAIL": "tester@example.com",
            "ATLASSIAN_API_TOKEN": FAKE_JIRA_TOKEN, "JIRA_PROJECT_KEY": "SPEC", "CONFLUENCE_SPACE_KEY": "UAT"}


def pytest_configure(config):
    config.addinivalue_line("markers", "live: needs real keys in .env and the network")


class FakeJira:
    """Answers get_issue from saved real tickets (tests/agent/fixtures/jira), or from `issues`.
    `errors` is a list of exceptions raised by the first calls, in order."""

    def __init__(self, issues=None, errors=()):
        self.issues = issues or {}
        self.errors = list(errors)
        self.calls = []

    def get_issue(self, key, fields=None):
        self.calls.append(key)
        if self.errors:
            raise self.errors.pop(0)
        if key in self.issues:
            return self.issues[key]
        path = FIXTURES / f"{key}.json"
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
        raise JiraError(f"GET /rest/api/3/issue/{key} -> 404", 404)


def fake_intake(jira=None):
    return intake.make_node(env=JIRA_ENV, client=jira or FakeJira(), sleep=lambda s: None)


@pytest.fixture
def records(tmp_path):
    return tmp_path / "runs"


@pytest.fixture
def brain_calls():
    return []


@pytest.fixture
def fake_brain(brain_calls):
    """Stands in for preflight.check_brain: no network, records how it was called."""
    def check(env=None, network=True):
        brain_calls.append(network)
        return {"brain": "llm", "provider": "openrouter", "model": "google/gemini-3.8-flash",
                "network_checked": network, "key_limit_remaining": None, "credit_remaining": 5.0, "warnings": []}
    return check


@pytest.fixture
def start(records, fake_brain):
    """run_ticket with test defaults: temp records folder, fake brain, fake Jira (saved tickets), default settings."""
    from specbridge.agent.graph import run_ticket

    def run(ticket_ref="SPEC-1", **kwargs):
        kwargs.setdefault("records_dir", records)
        kwargs.setdefault("brain_check", fake_brain)
        kwargs.setdefault("settings", Settings())
        kwargs.setdefault("env", {"BRAIN": "llm", "OPENROUTER_API_KEY": FAKE_KEY})
        kwargs["nodes"] = {"intake": fake_intake(), **(kwargs.get("nodes") or {})}
        return run_ticket(ticket_ref, **kwargs)
    return run
