import json
import sys
from pathlib import Path

import pytest

PROJECT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT))

from specbridge.agent.limits import Settings  # noqa: E402
from specbridge.agent.nodes import intake, orchestrator, understand  # noqa: E402
from specbridge.atlassian import JiraError  # noqa: E402
from specbridge.brain import BrainError, Reply  # noqa: E402

FAKE_KEY = "AIza-TESTKEY-must-never-appear"
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


def plain_answer(**changes):
    """A valid understand answer: one stated criterion, one known screen, fits, testable."""
    return {"intent": "Make the thing work", "criteria": [{"text": "The thing works", "source": "stated",
                                                          "quote": "", "status": "ok"}],
            "screens": [{"name": "Patient chart", "role": "changed", "status": "existing", "matches": ""}], "roles": ["clinician"], "questions": [],
            "risks": [], "domain_fit": "fits", "domain_reason": "clinical feature", "testable": True,
            "reason": "clear criteria", **changes}


class FakeBrain:
    """Stands in for the AI: returns `answer` (a dict, or a function of the user prompt) or raises `error`."""

    def __init__(self, answer=None, error=None, cost=0.0012):
        self.answer, self.error, self.cost = answer if answer is not None else plain_answer(), error, cost
        self.calls = []

    def ask_json(self, prompt, schema, system=None, max_tokens=4000, temperature=0.0):
        self.calls.append({"prompt": prompt, "system": system, "schema": schema, "max_tokens": max_tokens})
        if self.error:
            raise self.error
        data = self.answer(prompt) if callable(self.answer) else self.answer
        return Reply(text="{}", data=data, brain="llm", provider="google", model="fake/model",
                     input_tokens=900, output_tokens=300, cost_usd=self.cost, seconds=0.01, attempts=1, byok=False)


KNOWN_SCREENS = [("patient-chart", "widget allergies-details-widget in patient-chart-allergies-dashboard-slot"),
                 ("patient-chart", "workspace patient-allergy-form-workspace titled Record an allergy"),
                 ("billing-app", "workspace billing-form-workspace")]


def fake_understand(brain=None, lookup=None, catalogue=None):
    """understand with a fake brain; lookup None = every screen found, or a function name -> [(repo, path)];
    catalogue = the registered screens shown to the AI (text -> [(repo, line)])."""
    return understand.make_node(brain=brain or FakeBrain(), env={},
                                lookup=lookup or (lambda name: [("patient-chart", "src/x.tsx")]),
                                catalogue=catalogue or (lambda text: KNOWN_SCREENS))


def fake_search(files_by_word=None):
    """A stand-in for the code search: each word of the query found in files_by_word adds its files, in order;
    unknown queries get two generic files. Returns hits shaped like CodeIndex.search_code."""
    files_by_word = files_by_word or {}

    def search(text, k):
        paths = []
        for word, files in files_by_word.items():
            if word in text.lower():
                paths += [f for f in files if f not in paths]
        paths = paths or ["src/app/root.component.tsx", "src/app/config-schema.ts"]
        return [{"repo": "patient-chart", "path": p, "piece": p.split("/")[-1].split(".")[0], "kind": "component",
                 "lines": [1, 40], "appears_in": [], "found_by": "search"} for p in paths[:k]]
    search.mode = "fake"
    return search


def fake_orchestrator(brain=None, search=None):
    return orchestrator.make_node(brain=brain or FakeBrain(), env={}, search=search or fake_search())


def fake_intake(jira=None):
    return intake.make_node(env=JIRA_ENV, client=jira or FakeJira(), sleep=lambda s: None)


@pytest.fixture(autouse=True)
def no_network(request, monkeypatch):
    """Offline tests must never reach Jira, OpenRouter or Ollama; only tests marked `live` may."""
    if request.node.get_closest_marker("live"):
        return

    def blocked(*args, **kwargs):
        raise AssertionError("network call in an offline test (mark it @pytest.mark.live)")
    monkeypatch.setattr("urllib.request.urlopen", blocked)


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
        return {"brain": "llm", "provider": "google", "model": "gemini-3.8-flash", "network_checked": network,
                "warnings": []}
    return check


@pytest.fixture
def start(records, fake_brain):
    """run_ticket with test defaults: temp records folder, fake brain check, fake Jira (saved tickets), fake AI,
    default settings. Nothing here reaches the network."""
    from specbridge.agent.graph import run_ticket

    def run(ticket_ref="SPEC-1", **kwargs):
        kwargs.setdefault("records_dir", records)
        kwargs.setdefault("brain_check", fake_brain)
        kwargs.setdefault("settings", Settings())
        kwargs.setdefault("env", {"BRAIN": "llm", "GEMINI_API_KEY": FAKE_KEY})
        kwargs["nodes"] = {"intake": fake_intake(), "understand": fake_understand(), "orchestrator": fake_orchestrator(),
                           **(kwargs.get("nodes") or {})}
        return run_ticket(ticket_ref, **kwargs)
    return run
