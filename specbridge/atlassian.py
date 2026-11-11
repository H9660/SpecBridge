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

    # --- used only by the agent's publish node (D2: the only code that writes) -----------------------------

    def find_pages(self, labels, space_key=None):
        """Pages in the space (default: the configured one) carrying every label: [{id, title}]."""
        cql = f'space = "{space_key or self.space}" and type = page and ' + " and ".join(f'label = "{l}"' for l in labels)
        data = self.request("GET", "/wiki/rest/api/content/search?" + urllib.parse.urlencode({"cql": cql, "limit": 5}))
        return [{"id": str(r["id"]), "title": r.get("title", "")} for r in data.get("results", [])]

    def find_page_by_title(self, space_id, title):
        query = urllib.parse.urlencode({"space-id": space_id, "title": title, "status": "current"})
        data = self.request("GET", f"/wiki/api/v2/pages?{query}")
        return [{"id": str(r["id"]), "title": r.get("title", "")} for r in data.get("results", [])]

    def get_page(self, page_id):
        """{id, title, version: {number, message, authorId}} (no body)."""
        return self.request("GET", f"/wiki/api/v2/pages/{urllib.parse.quote(str(page_id))}")

    def create_page(self, space_id, title, storage):
        return self.request("POST", "/wiki/api/v2/pages", {
            "spaceId": space_id, "status": "current", "title": title,
            "body": {"representation": "storage", "value": storage}})

    def update_page(self, page_id, title, storage, version, message):
        return self.request("PUT", f"/wiki/api/v2/pages/{urllib.parse.quote(str(page_id))}", {
            "id": str(page_id), "status": "current", "title": title,
            "body": {"representation": "storage", "value": storage},
            "version": {"number": version, "message": message}})

    def add_labels(self, page_id, labels):
        return self.request("POST", f"/wiki/rest/api/content/{urllib.parse.quote(str(page_id))}/label",
                            [{"prefix": "global", "name": l} for l in labels])

    def get_property(self, page_id, key):
        """The page's content property `key` as {id, value, version: {number}}, or None."""
        query = urllib.parse.urlencode({"key": key})
        data = self.request("GET", f"/wiki/api/v2/pages/{urllib.parse.quote(str(page_id))}/properties?{query}")
        found = data.get("results", [])
        return found[0] if found else None

    def set_property(self, page_id, key, value, current=None):
        base = f"/wiki/api/v2/pages/{urllib.parse.quote(str(page_id))}/properties"
        if current:
            return self.request("PUT", f"{base}/{current['id']}", {
                "key": key, "value": value, "version": {"number": current["version"]["number"] + 1}})
        return self.request("POST", base, {"key": key, "value": value})

    def add_page_comment(self, page_id, storage):
        return self.request("POST", "/wiki/api/v2/footer-comments", {
            "pageId": str(page_id), "body": {"representation": "storage", "value": storage}})

    def issue_comments(self, key):
        query = urllib.parse.urlencode({"maxResults": 100, "orderBy": "-created"})
        return self.request("GET", f"/rest/api/3/issue/{urllib.parse.quote(key)}/comment?{query}").get("comments", [])

    def add_comment(self, key, adf):
        return self.request("POST", f"/rest/api/3/issue/{urllib.parse.quote(key)}/comment", {"body": adf})

    def update_comment(self, key, comment_id, adf):
        return self.request("PUT", f"/rest/api/3/issue/{urllib.parse.quote(key)}/comment/"
                                   f"{urllib.parse.quote(str(comment_id))}", {"body": adf})
