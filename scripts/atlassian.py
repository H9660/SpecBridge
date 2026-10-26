"""Small client for the team's own Atlassian site (Jira + Confluence), configured from .env."""
import base64
import json
import pathlib
import sys
import urllib.error
import urllib.request

PROJECT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT))
from specbridge.env import load_env  # noqa: E402,F401

REQUIRED = ("ATLASSIAN_SITE", "ATLASSIAN_EMAIL", "ATLASSIAN_API_TOKEN", "JIRA_PROJECT_KEY", "CONFLUENCE_SPACE_KEY")


def missing_settings(env):
    return [k for k in REQUIRED if not env.get(k)]


class Atlassian:
    def __init__(self, env):
        self.site = env["ATLASSIAN_SITE"].rstrip("/")
        self.project = env["JIRA_PROJECT_KEY"]
        self.space = env["CONFLUENCE_SPACE_KEY"]
        token = base64.b64encode(f"{env['ATLASSIAN_EMAIL']}:{env['ATLASSIAN_API_TOKEN']}".encode()).decode()
        self.headers = {"Authorization": f"Basic {token}", "Accept": "application/json",
                        "Content-Type": "application/json"}

    def request(self, method, path, body=None):
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(f"{self.site}{path}", data=data, method=method, headers=self.headers)
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                raw = resp.read()
                return json.loads(raw) if raw else None
        except urllib.error.HTTPError as err:
            raise RuntimeError(f"{method} {path} -> {err.code}: {err.read().decode(errors='ignore')[:300]}") from None

    def whoami(self):
        return self.request("GET", "/rest/api/3/myself")

    def issue_types(self):
        """Issue type name -> id for the configured Jira project."""
        data = self.request("GET", f"/rest/api/3/issue/createmeta/{self.project}/issuetypes")
        return {t["name"]: t["id"] for t in data.get("issueTypes", data.get("values", []))}

    def confluence_space(self):
        data = self.request("GET", f"/wiki/api/v2/spaces?keys={self.space}")
        return data["results"][0] if data.get("results") else None

    def search(self, jql, fields="summary,labels"):
        issues, token = [], None
        while True:
            body = {"jql": jql, "fields": fields.split(","), "maxResults": 100}
            if token:
                body["nextPageToken"] = token
            data = self.request("POST", "/rest/api/3/search/jql", body)
            issues += data["issues"]
            token = data.get("nextPageToken")
            if not token:
                return issues

    def create_issue(self, fields):
        return self.request("POST", "/rest/api/3/issue", {"fields": fields})
