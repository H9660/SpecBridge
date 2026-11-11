import json
import sys
from pathlib import Path

import pytest

PROJECT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT))

from specbridge.agent.limits import Settings  # noqa: E402
from specbridge.agent.nodes import intake, merge, orchestrator, publish, reviewer, understand  # noqa: E402
from specbridge.atlassian import JiraError  # noqa: E402
from specbridge.brain import BrainError, Reply  # noqa: E402

FAKE_KEY = "AIza-TESTKEY-must-never-appear"
FAKE_JIRA_TOKEN = "jira-token-must-never-appear"
FIXTURES = Path(__file__).parent / "fixtures" / "jira"
JIRA_ENV = {"ATLASSIAN_SITE": "https://rooks101.atlassian.net", "ATLASSIAN_EMAIL": "tester@example.com",
            "ATLASSIAN_API_TOKEN": FAKE_JIRA_TOKEN, "JIRA_PROJECT_KEY": "SPEC", "CONFLUENCE_SPACE_KEY": "UAT"}


def pytest_configure(config):
    config.addinivalue_line("markers", "live: needs real keys in .env and the network")


class FakeAtlassian:
    """Stands in for the team's Confluence space and Jira project (publish): pages with versions, labels,
    properties and comments; Jira comments. `errors` maps a method name to the exception it raises."""

    def __init__(self, space=True, errors=None, me="acc-specbridge"):
        self.site, self.space, self.space_key = JIRA_ENV["ATLASSIAN_SITE"], "UAT", "UAT"
        self.has_space, self.errors, self.me = space, dict(errors or {}), me
        self.pages, self.jira_comments, self.calls, self.next_id = {}, {}, [], 1000

    def _call(self, name, *args):
        self.calls.append(name)
        if name in self.errors:
            raise self.errors[name]

    def _id(self):
        self.next_id += 1
        return str(self.next_id)

    def confluence_space(self):
        self._call("confluence_space")
        return {"id": "SP1", "key": self.space_key} if self.has_space else None

    def whoami(self):
        self._call("whoami")
        return {"accountId": self.me}

    def find_pages(self, labels, space_key=None):
        self._call("find_pages")
        self.searched_space = space_key
        return [{"id": i, "title": p["title"]} for i, p in self.pages.items() if set(labels) <= p["labels"]]

    def find_page_by_title(self, space_id, title):
        self._call("find_page_by_title")
        return [{"id": i, "title": p["title"]} for i, p in self.pages.items() if p["title"] == title]

    def get_page(self, page_id):
        self._call("get_page")
        p = self.pages[page_id]
        return {"id": page_id, "title": p["title"], "version": dict(p["version"])}

    def create_page(self, space_id, title, storage):
        self._call("create_page")
        if any(p["title"] == title for p in self.pages.values()):
            raise JiraError("POST /wiki/api/v2/pages -> 400: title already exists", 400)
        page_id = self._id()
        self.pages[page_id] = {"title": title, "storage": storage, "version": {"number": 1, "message": ""},
                               "labels": set(), "props": {}, "comments": []}
        return {"id": page_id, "version": {"number": 1}}

    def update_page(self, page_id, title, storage, version, message):
        self._call("update_page")
        p = self.pages[page_id]
        if version != p["version"]["number"] + 1:
            raise JiraError("PUT page -> 409: version conflict", 409)
        p.update(title=title, storage=storage, version={"number": version, "message": message})
        return {"id": page_id, "version": {"number": version}}

    def add_labels(self, page_id, labels):
        self._call("add_labels")
        self.pages[page_id]["labels"] |= set(labels)

    def get_property(self, page_id, key):
        self._call("get_property")
        return self.pages[page_id]["props"].get(key)

    def set_property(self, page_id, key, value, current=None):
        self._call("set_property")
        props = self.pages[page_id]["props"]
        number = props[key]["version"]["number"] + 1 if key in props else 1
        props[key] = {"id": f"prop-{page_id}", "key": key, "value": value, "version": {"number": number}}

    def add_page_comment(self, page_id, storage):
        self._call("add_page_comment")
        self.pages[page_id]["comments"].append(storage)
        return {"id": self._id()}

    def edit_by_person(self, page_id, storage="<p>edited by the PM</p>"):
        """A person edits the page in Confluence: a new version without SpecBridge's mark."""
        p = self.pages[page_id]
        p.update(storage=storage, version={"number": p["version"]["number"] + 1, "message": ""})

    def issue_comments(self, key):
        self._call("issue_comments")
        return list(self.jira_comments.get(key, []))

    def add_comment(self, key, adf):
        self._call("add_comment")
        c = {"id": self._id(), "author": {"accountId": self.me}, "body": adf}
        self.jira_comments.setdefault(key, []).append(c)
        return c

    def update_comment(self, key, comment_id, adf):
        self._call("update_comment")
        for c in self.jira_comments.get(key, []):
            if c["id"] == comment_id:
                c["body"] = adf
                return c
        raise JiraError("PUT comment -> 404", 404)

    def writes(self):
        return [c for c in self.calls if c in ("create_page", "update_page", "add_labels", "set_property",
                                               "add_page_comment", "add_comment", "update_comment")]


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


def review_ok(prompt):
    """A fake reviewer reply: the one criterion of this call (its prompt starts "## AC1: ...") is ok."""
    return {"criteria": [{"id": prompt.split(":")[0][3:], "verdict": "ok", "problems": [], "retry_hint": ""}]}


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


def fake_worker(status="complete"):
    """Stands in for criterion_worker in graph tests: one case per criterion, citing E1."""
    def run(payload, settings):
        item = payload["work_item"]
        return {"work_item_id": item["id"], "criterion_ids": item["criterion_ids"], "round": payload.get("round", 1),
                "status": status, "cases": [{"id": f"{item['id']}-C{n}", "criterion_id": cid, "title": f"check {cid}",
                                             "type": "happy", "preconditions": [], "steps": ["open it"],
                                             "expected": "it works", "evidence_ids": ["E1"]}
                                            for n, cid in enumerate(item["criterion_ids"], 1)],
                "evidence": [{"id": "E1", "repo": "patient-chart", "path": "src/x.tsx", "lines": [1, 5]}],
                "questions": [], "notes": [], "spent": {"tokens": 500, "cost": 0.002}}
    return run


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
        kwargs.setdefault("atlassian_check", lambda env=None, network=True: {"site": "fake", "network_checked": False})
        kwargs.setdefault("settings", Settings())
        kwargs.setdefault("env", {"BRAIN": "llm", "GEMINI_API_KEY": FAKE_KEY})
        kwargs["nodes"] = {"intake": fake_intake(), "understand": fake_understand(), "orchestrator": fake_orchestrator(),
                           "criterion_worker": fake_worker(), "e2e_worker": fake_worker(),
                           "merge": merge.make_node(brain=FakeBrain({"remove": [], "rename": []}), env={}),
                           "reviewer": reviewer.make_node(brain=FakeBrain(review_ok), env={}, facts=None),
                           "publish": publish.make_node(client=FakeAtlassian(), env=JIRA_ENV, records_dir=records),
                           **(kwargs.get("nodes") or {})}
        return run_ticket(ticket_ref, **kwargs)
    return run
