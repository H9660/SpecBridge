"""publish (node 11, code only: no AI): in live mode, put the page render made on Confluence and one comment on the
ticket. The only node that writes outside this machine (D2), and only to the team's own site (D4): pages in the
configured space (UAT) and comments on the ticket being processed.

Before any write, plain checks (nothing is published if one fails): live mode; the ticket is in the configured
Jira project on the configured site; there is a page; its storage copy is well-formed XML; the page and the comment
hold no secret-like text.
Page (D10): found by its labels (the ticket key + "specbridge"), else by its exact title. A new page is created
with the labels. An existing page is updated only if SpecBridge wrote its current version (the version number kept
in the page property "specbridge", or a version message starting "[SpecBridge]"); if a person edited it since,
nothing is overwritten and the new draft goes in as a comment on the page.
Jira: one comment per ticket, found by its "[SpecBridge]" marker among this account's comments, updated on re-runs;
{page_url} is filled in with the page's address.
If publishing fails, the page is saved locally instead (as save_local does), so the work is never lost.
Out: state["published"] = {page_id, page_url, page_action, page_version, comment_id, comment_action, error,
fallback}.
"""
import re

from specbridge import ticket_text
from specbridge.agent.nodes import save_local
from specbridge.agent.nodes.clarify import COMMENT_MARKER, PAGE_LINK
from specbridge.atlassian import Atlassian, missing_settings
from specbridge.env import load_env

PROPERTY = "specbridge"
VERSION_MARK = "[SpecBridge]"
MAX_STORAGE = 2_000_000          # far below Confluence's limit; a bigger page means something went wrong


class PublishRefused(Exception):
    pass


def page_url(client, page_id, space_key=None):
    """The page's address, with the space key Confluence reports (the configured key may be an old alias)."""
    return f"{client.site}/wiki/spaces/{space_key or client.space}/pages/{page_id}"


def checks(state, env):
    """Raise PublishRefused unless the run may publish."""
    if state.get("mode") != "live":
        raise PublishRefused(f"publish runs only in live mode (this run: {state.get('mode')!r})")
    missing = missing_settings(env)
    if missing:
        raise PublishRefused(f"missing settings in .env: {', '.join(missing)}")
    ticket, page = state.get("ticket") or {}, state.get("page") or {}
    key, project = str(ticket.get("key") or ""), env["JIRA_PROJECT_KEY"]
    if not re.fullmatch(rf"{re.escape(project)}-\d+", key):
        raise PublishRefused(f"ticket {key or '?'} is not in project {project}")
    site = env["ATLASSIAN_SITE"].rstrip("/")
    if ticket.get("url") and not str(ticket["url"]).startswith(site + "/"):
        raise PublishRefused("the ticket is not on the configured Atlassian site")
    if not page.get("storage") or not page.get("title"):
        raise PublishRefused("there is no page to publish")
    if len(page["storage"]) > MAX_STORAGE:
        raise PublishRefused(f"the page is {len(page['storage']):,} characters; at most {MAX_STORAGE:,} are allowed")
    if not save_local.well_formed(page["storage"]):
        raise PublishRefused("the page is not well-formed XML")
    for name, text in (("page", page["storage"]), ("title", page["title"]), ("comment", page.get("comment", ""))):
        if ticket_text.redact_secrets(text)[1]:
            raise PublishRefused(f"the {name} contains secret-like text")
    return key


def comment_adf(text, url):
    """Plain text -> Atlassian document format: one paragraph per line, the page address as a link."""
    paragraphs = []
    for line in text.replace(PAGE_LINK, url).split("\n"):
        if not line.strip():
            continue
        parts = line.split(url) if url else [line]
        content = []
        for n, part in enumerate(parts):
            if part:
                content.append({"type": "text", "text": part})
            if n < len(parts) - 1:
                content.append({"type": "text", "text": url, "marks": [{"type": "link", "attrs": {"href": url}}]})
        paragraphs.append({"type": "paragraph", "content": content})
    return {"type": "doc", "version": 1, "content": paragraphs}


def adf_text(node):
    if isinstance(node, dict):
        return (node.get("text") or "") + "".join(adf_text(c) for c in node.get("content") or [])
    return ""


def draft_comment(storage, run_id):
    note = (f'<ac:structured-macro ac:name="info"><ac:parameter ac:name="title">New SpecBridge draft (run '
            f'{run_id})</ac:parameter><ac:rich-text-body><p>This page was edited by a person after SpecBridge last '
            f'wrote it, so it was not overwritten. The new draft is below.</p></ac:rich-text-body>'
            f'</ac:structured-macro>')
    return note + storage


def put_page(client, state, page):
    """(page_id, action, version, space key). Creates, updates, or - if a person edited the page - comments on it."""
    run_id = state.get("run_id", "?")
    message = f"{VERSION_MARK} run {run_id}"
    space = client.confluence_space()
    if not space:
        raise PublishRefused(f"Confluence space {client.space} was not found")
    key = space.get("key") or client.space
    found = client.find_pages(page["labels"][:2], key)
    if not found:
        found = client.find_page_by_title(space["id"], page["title"])
    if not found:
        made = client.create_page(space["id"], page["title"], page["storage"])
        page_id, version = str(made["id"]), (made.get("version") or {}).get("number", 1)
        client.add_labels(page_id, page["labels"])
        client.set_property(page_id, PROPERTY, {"page_version": version, "run_id": run_id})
        return page_id, "created", version, key
    page_id = found[0]["id"]
    current = client.get_page(page_id)
    number = (current.get("version") or {}).get("number", 1)
    prop = client.get_property(page_id, PROPERTY)
    ours = (prop and (prop.get("value") or {}).get("page_version") == number) or \
        str((current.get("version") or {}).get("message") or "").startswith(VERSION_MARK)
    if not ours:
        client.add_page_comment(page_id, draft_comment(page["storage"], run_id))
        return page_id, "draft-as-comment", number, key
    client.update_page(page_id, page["title"], page["storage"], number + 1, message)
    client.add_labels(page_id, page["labels"])
    client.set_property(page_id, PROPERTY, {"page_version": number + 1, "run_id": run_id}, prop)
    return page_id, "updated", number + 1, key


def put_comment(client, key, text, url):
    """(comment_id, action): this account's [SpecBridge] comment on the ticket, updated or created."""
    me = (client.whoami() or {}).get("accountId")
    adf = comment_adf(text, url)
    for c in client.issue_comments(key):
        if (c.get("author") or {}).get("accountId") == me and adf_text(c.get("body")).startswith(COMMENT_MARKER):
            client.update_comment(key, c["id"], adf)
            return str(c["id"]), "updated"
    made = client.add_comment(key, adf)
    return str(made["id"]), "created"


def publish(state, env, client, records_dir=None):
    out = {"page_id": None, "page_url": None, "page_action": None, "page_version": None,
           "comment_id": None, "comment_action": None, "error": "", "fallback": None}
    try:
        key = checks(state, env)
        page = state["page"]
        page_id, action, version, space_key = put_page(client, state, page)
        url = page_url(client, page_id, space_key)
        out.update(page_id=page_id, page_url=url, page_action=action, page_version=version)
        text = page.get("comment") or f"{COMMENT_MARKER} {key}: UAT page\nPage: {PAGE_LINK}"
        if action == "draft-as-comment":
            text += "\n(The page was edited by a person, so the new draft was added as a comment on the page.)"
        out["comment_id"], out["comment_action"] = put_comment(client, key, text, url)
    except PublishRefused as err:
        out["error"] = f"not published: {err}"
    except Exception as err:  # noqa: BLE001 - network or Atlassian errors: report, keep the run, save locally
        out["error"] = f"publishing failed: {type(err).__name__}: {str(err)[:300]}"
    if out["error"] and state.get("page"):
        out["fallback"] = save_local.save(state, records_dir or save_local.run_record.RUNS)
    return out


def make_node(client=None, env=None, records_dir=None):
    """Tests pass a fake client and env; the real node builds the Atlassian client from .env when it runs
    (building it makes no network call). records_dir: where the local fallback goes."""
    def node(state, settings):
        e = load_env() if env is None else env
        missing = missing_settings(e)
        c = client or (_NoClient(missing) if missing else Atlassian(e))
        return {"published": publish(state, e, c, records_dir)}
    return node


class _NoClient:
    """Stands in when the Atlassian settings are missing: checks() refuses before it is ever used."""

    def __init__(self, missing):
        self.missing = missing

    def __getattr__(self, name):
        raise PublishRefused(f"missing settings in .env: {', '.join(self.missing)}")


node = make_node()
