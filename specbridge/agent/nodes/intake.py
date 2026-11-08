"""intake (code, no AI): fetch the ticket from the team's own Jira and turn it into clean, safe text.

1. Read the reference: a ticket URL, a board link with selectedIssue=, or just the key (SPEC-12).
2. Scope (D4): https on exactly ATLASSIAN_SITE and project JIRA_PROJECT_KEY, checked before any call.
3. Fetch summary, type, status, labels, description (read-only; one retry on network / server errors).
4. Rich text -> plain text; secrets redacted before the text is kept anywhere; lines aimed at the AI
   flagged but kept (understand reports them as a risk, D3).
Out: state["ticket"] = {key, url, type, status, title, text, labels, flags[{kind, detail}]}.
A refusal or fetch failure raises IntakeError; the run ends with status "error".
"""
import re
import time
import urllib.error
import urllib.parse

from specbridge import ticket_text
from specbridge.atlassian import Atlassian, JiraError, missing_settings
from specbridge.env import load_env

NEEDED = ("ATLASSIAN_SITE", "ATLASSIAN_EMAIL", "ATLASSIAN_API_TOKEN", "JIRA_PROJECT_KEY")
KEY = re.compile(r"([A-Za-z][A-Za-z0-9_]*)-(\d+)")
MAX_TEXT_CHARS = 20_000
RETRY_STATUS = {429, 500, 502, 503, 504}


class IntakeError(RuntimeError):
    def __init__(self, message, retryable=False):
        super().__init__(message)
        self.retryable = retryable


# --- the reference ----------------------------------------------------------------------------------

def _key(project, number):
    return f"{project.upper()}-{int(number)}"


def parse_ref(ref, site, project):
    """The ticket key a reference points at, or IntakeError. Never touches the network."""
    ref = (ref or "").strip()
    site_url = urllib.parse.urlsplit(site.strip())
    if site_url.scheme != "https" or not site_url.hostname:
        raise IntakeError(f"ATLASSIAN_SITE must be an https:// address, not {site!r}")
    if "://" in ref or ref.lower().startswith("www.") or "/" in ref:
        parts = urllib.parse.urlsplit(ref if "://" in ref else "//" + ref)
        if parts.scheme != "https":
            raise IntakeError(f"use the full https:// link from {site_url.hostname}, or just the key (e.g. "
                              f"{project}-12)")
        try:
            port = parts.port
        except ValueError:
            port = -1
        if "@" in parts.netloc or (parts.hostname or "").lower() != site_url.hostname.lower() or port not in (None, 443):
            raise IntakeError(f"only tickets from https://{site_url.hostname} can be used")
        candidates = [seg for seg in parts.path.split("/")] + \
            [v.strip() for v in urllib.parse.parse_qs(parts.query).get("selectedIssue", [])]
    else:
        candidates = [ref]
    found = {_key(*m.groups()) for c in candidates if (m := KEY.fullmatch(c)) and int(m.group(2)) > 0}
    if not found:
        raise IntakeError(f"no ticket key found in {ref[:80]!r}; give a link to a ticket or a key like {project}-12")
    if len(found) > 1:
        raise IntakeError(f"the link points at more than one ticket ({', '.join(sorted(found))}); give just one")
    key = found.pop()
    if key.split("-")[0] != project.upper():
        raise IntakeError(f"only tickets from project {project} can be used, not {key}")
    return key


# --- fetching ---------------------------------------------------------------------------------------

def fetch(client, key, sleep=time.sleep):
    for attempt in (1, 2):
        try:
            return client.get_issue(key)
        except JiraError as err:
            if err.status == 404:
                raise IntakeError(f"{key} not found, or this Jira account cannot see it") from None
            if err.status in (401, 403):
                raise IntakeError("Jira rejected the login; check ATLASSIAN_EMAIL and ATLASSIAN_API_TOKEN in .env") from None
            if err.status not in RETRY_STATUS or attempt == 2:
                raise IntakeError(f"Jira answered HTTP {err.status} for {key}; try again later",
                                  retryable=err.status in RETRY_STATUS) from None
        except (urllib.error.URLError, TimeoutError, OSError) as err:
            if attempt == 2:
                reason = getattr(err, "reason", None) or type(err).__name__
                raise IntakeError(f"cannot reach Jira ({reason}); check the internet connection and resume",
                                  retryable=True) from None
        sleep(2)


# --- cleaning ---------------------------------------------------------------------------------------

def clean_issue(issue, site, project):
    """Jira's answer -> the Ticket dict (redacted, flagged)."""
    key = issue.get("key", "")
    if key.split("-")[0] != project.upper():   # an issue moved to another project answers with its new key
        raise IntakeError(f"the ticket now lives at {key}, outside project {project}")
    f = issue.get("fields") or {}
    flags = []
    body, counts = ticket_text.adf_to_text(f.get("description"))
    title, n_title = ticket_text.redact_secrets((f.get("summary") or "").strip())
    body, n_body = ticket_text.redact_secrets(body)
    labels = []
    n_labels = 0
    for label in f.get("labels") or []:
        clean, n = ticket_text.redact_secrets(label)
        labels.append(clean)
        n_labels += n
    if n_title + n_body + n_labels:
        flags.append({"kind": "secret-redacted", "detail": f"{n_title + n_body + n_labels} secret(s) replaced by "
                                                           f"{ticket_text.REDACTED}"})
    if not body:
        flags.append({"kind": "empty-description", "detail": "the ticket has a summary only"})
    if len(body) > MAX_TEXT_CHARS:
        cut = body.rfind("\n", 0, MAX_TEXT_CHARS)
        cut = cut if cut > MAX_TEXT_CHARS // 2 else MAX_TEXT_CHARS
        flags.append({"kind": "truncated", "detail": f"description cut from {len(body):,} to {cut:,} characters"})
        body = body[:cut].rstrip() + "\n[... rest of the description cut ...]"
    if counts["attachments"]:
        flags.append({"kind": "attachments-dropped", "detail": f"{counts['attachments']} image(s) or file(s) not read"})
    text = f"{title}\n\n{body}" if body else title
    lines = ticket_text.instruction_lines(text)
    if lines:
        flags.append({"kind": "possible-injection",
                      "detail": f"{len(lines)} line(s) look like instructions to the AI (line {', '.join(map(str, lines))}); "
                                "kept as data, not followed"})
    names = ticket_text.file_names(text)
    if names:
        flags.append({"kind": "mentions-files", "detail": f"names {len(names)} code file(s)"})
    return {"key": key, "url": f"{site.rstrip('/')}/browse/{key}",
            "type": (f.get("issuetype") or {}).get("name", ""), "status": (f.get("status") or {}).get("name", ""),
            "title": title, "text": text, "labels": labels, "flags": flags}


# --- the node ---------------------------------------------------------------------------------------

def make_node(env=None, client=None, sleep=time.sleep):
    """intake as a graph node. Tests pass env, a fake client and a no-op sleep."""
    def node(state, settings):
        e = load_env() if env is None else env
        missing = missing_settings(e, NEEDED)
        if missing:
            raise IntakeError(f"intake needs {', '.join(missing)} in .env")
        key = parse_ref(state.get("ticket_ref"), e["ATLASSIAN_SITE"], e["JIRA_PROJECT_KEY"])
        issue = fetch(client or Atlassian(e), key, sleep)
        return {"ticket": clean_issue(issue, e["ATLASSIAN_SITE"], e["JIRA_PROJECT_KEY"])}
    return node


node = make_node()
