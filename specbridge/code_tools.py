"""Code-reading tools the agent can call: search the code library, read a file, grep, find usages.

Each tool takes JSON-style arguments and returns plain data, so it can be offered to any brain
that supports tool calls (TOOLS holds the schemas). Only files in the index can be read, which
keeps the agent inside the five frozen repos.
"""
import re
import subprocess

MAX_LINES = 400
MAX_MATCHES = 50

# TODO WE ARE NOT VALIDATING THE OUTPUT SCHEMA HERE. IT SHOULD BE VALIDATED. BUT WE CAN DO IT IN SOME OTHER PROPER FILE AS WELL.
TOOLS = [
    {"name": "search_code", "description": "Find the code behind a screen or behaviour described in plain words "
     "(e.g. a ticket). Returns the best files with their best-matching piece and where they appear in the app.",
     "input_schema": {"type": "object", "required": ["query"], "properties": {
         "query": {"type": "string"}, "k": {"type": "integer", "default": 10},
         "repos": {"type": "array", "items": {"type": "string"}}}}},
    {"name": "read_file", "description": "Read lines of a file in one of the repos (at most 400 lines per call).",
     "input_schema": {"type": "object", "required": ["repo", "path"], "properties": {
         "repo": {"type": "string"}, "path": {"type": "string"},
         "start_line": {"type": "integer", "default": 1}, "end_line": {"type": "integer"}}}},
    {"name": "grep", "description": "Search the repos for an exact text or regular expression (e.g. a label shown "
     "on screen, a function name). Returns file, line number and the matching line.",
     "input_schema": {"type": "object", "required": ["pattern"], "properties": {
         "pattern": {"type": "string"}, "repos": {"type": "array", "items": {"type": "string"}},
         "ignore_case": {"type": "boolean", "default": False}}}},
    {"name": "find_usages", "description": "Files linked to a file: what it imports, what imports it, and UI wiring "
     "(slots, workspaces, modals), including across repos.",
     "input_schema": {"type": "object", "required": ["repo", "path"], "properties": {
         "repo": {"type": "string"}, "path": {"type": "string"}}}},
]


class CodeTools:
    def __init__(self, index, embedder=None):
        self.index, self.embedder = index, embedder

    def call(self, name, args):
        if name not in {t["name"] for t in TOOLS}:
            return {"error": f"unknown tool {name!r}"}
        try:
            return getattr(self, name)(**args)
        except TypeError as err:
            return {"error": f"bad arguments for {name}: {err}"}

    def search_code(self, query, k=10, repos=None):
        return {"results": self.index.search_code(query, k, self.embedder, repos)}

    def read_file(self, repo, path, start_line=1, end_line=None):
        row = self.index.db.execute("SELECT text FROM files WHERE repo = ? AND path = ?", (repo, path)).fetchone()
        if not row:
            return {"error": f"{repo}/{path} is not a code file in the library"}
        lines = row[0].splitlines()
        start = max(1, int(start_line))
        end = min(len(lines), int(end_line) if end_line else start + MAX_LINES - 1, start + MAX_LINES - 1)
        return {"repo": repo, "path": path, "start_line": start, "end_line": end, "total_lines": len(lines),
                "text": "\n".join(f"{n}: {lines[n - 1]}" for n in range(start, end + 1))}

    def grep(self, pattern, repos=None, ignore_case=False):
        try:
            re.compile(pattern)
        except re.error as err:
            return {"error": f"bad pattern: {err}"}
        matches = []
        for repo in repos or self.index.repos:
            if repo not in self.index.repos:
                return {"error": f"unknown repo {repo!r}"}
            args = ["git", "-C", str(self.index.workdir / repo), "grep", "-n", "-I", "-E", "--max-count", "5"]
            out = subprocess.run(args + (["-i"] if ignore_case else []) + ["-e", pattern, "--", "*.ts", "*.tsx",
                                 "*.js", "*.jsx", "*.json"], capture_output=True, text=True, encoding="utf-8").stdout
            for line in out.splitlines():
                path, num, text = line.split(":", 2)
                matches.append({"repo": repo, "path": path, "line": int(num), "text": text.strip()[:200]})
        return {"matches": matches[:MAX_MATCHES], "truncated": len(matches) > MAX_MATCHES}

    def find_usages(self, repo, path):
        rows = self.index.neighbours(repo, path)
        if not rows and not self.index.db.execute(
                "SELECT 1 FROM files WHERE repo = ? AND path = ?", (repo, path)).fetchone():
            return {"error": f"{repo}/{path} is not a code file in the library"}
        return {"links": [{"repo": r, "path": p, "kind": k, "direction": d, "via": v} for r, p, k, d, v in rows]}
