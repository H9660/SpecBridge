"""Small client for the team's own Atlassian site (Jira + Confluence), configured from .env.

Used by the agent (intake reads tickets; publish will write pages and comments) and by the setup scripts.
Errors carry the HTTP status but never the credentials.
"""
import base64
import json
import urllib.error
import urllib.parse
import urllib.request

REQUIRED = ("ATLASSIAN_SITE", "ATLASSIAN_EMAIL", "ATLASSIAN_API_TOKEN", "JIRA_PROJECT_KEY", "CONFLUENCE_SPACE_KEY")


class JiraError(RuntimeError):
    def __init__(self, message, status=None):
        super().__init__(message)
        self.status = status


def missing_settings(env, required=REQUIRED):
    return [k for k in required if not env.get(k)]


class Atlassian:
    def __init__(self, env, timeout=60):
        self.site = env["ATLASSIAN_SITE"].rstrip("/")
        self.project = env["JIRA_PROJECT_KEY"]
        self.space = env.get("CONFLUENCE_SPACE_KEY")
        self.timeout = timeout
        token = base64.b64encode(f"{env['ATLASSIAN_EMAIL']}:{env['ATLASSIAN_API_TOKEN']}".encode()).decode()
        self.headers = {"Authorization": f"Basic {token}", "Accept": "application/json",
                        "Content-Type": "application/json"}

    def request(self, method, path, body=None):
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(f"{self.site}{path}", data=data, method=method, headers=self.headers)
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                raw = resp.read()
                return json.loads(raw) if raw else None
        except urllib.error.HTTPError as err:
            detail = err.read().decode(errors="ignore")[:300]
            raise JiraError(f"{method} {path} -> {err.code}: {detail}", err.code) from None

    def whoami(self):
        return self.request("GET", "/rest/api/3/myself")

    def get_issue(self, key, fields="summary,issuetype,status,labels,description"):
        """One issue, read-only: {key, fields: {...}}."""
        query = urllib.parse.urlencode({"fields": fields})
        return self.request("GET", f"/rest/api/3/issue/{urllib.parse.quote(key)}?{query}")

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
