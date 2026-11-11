"""render (node 9, code only: no AI, no network): the finished state -> the UAT page and the Jira comment.

Every finished run gets a page: a test plan (the reviewer's final verdict), a questions-only page (clarify), or a
short page with the reason (the orchestrator stopped before any worker ran).
One document (a list of blocks) is built once and written three ways:
  storage   Confluence storage format (XHTML), sent as is by publish (node 11)
  html      a standalone HTML page,  written to a file by save_local (node 10)
  markdown  a Markdown copy,          written to a file by save_local (node 10)
plus the plain-text Jira comment (with the {page_url} placeholder that publish fills in).
All text from the ticket, the AI and the code is redacted again and escaped, so it never becomes markup (D3);
questions and notes that read like instructions to an AI are left out. The same state and clock give the same
output, byte for byte.
Out: state["page"] = {title, labels, storage, html, markdown, comment, summary}.
"""
import html as _html
import json
import re
import time

from specbridge import ticket_text
from specbridge.agent.nodes.clarify import COMMENT_MARKER, PAGE_LINK, MAX_COMMENT_CHARS
from specbridge.agent.run_record import SNAPSHOTS

VERSION = "render-v1"
MAX_TITLE = 200                  # Confluence allows 255
LABEL_OK = re.compile(r"[^a-z0-9_-]+")
_BAD_XML = re.compile("[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
TONES = ("ok", "warn", "stop", "info", "grey")
VERDICT_TAG = {"ok": ("ok", "OK"), "weak": ("warn", "NEEDS ATTENTION"), "untestable": ("grey", "UNTESTABLE"),
               "skipped": ("grey", "SKIPPED"), "uncovered": ("stop", "NO TEST CASES"), "failed": ("stop", "NO TEST CASES"),
               "covered": ("info", "NOT REVIEWED"), "regression": ("info", "REGRESSION CHECK")}
TYPE_NAME = {"happy": "happy path", "negative": "negative", "edge": "edge case", "permission": "permission",
             "empty-state": "empty state", "e2e": "end-to-end flow"}
SCOPE_TEXT = {"full": "Full: new or changed behaviour on screen.",
              "regression": "Regression check: the change is behind the screens, so check that they still work as before."}
CASE_HEADERS = ["ID", "Preconditions", "Steps", "Expected result", "Actual result", "Pass/Fail"]


# --- safe text ----------------------------------------------------------------------------------------

def safe(text):
    """Untrusted text (ticket, AI, code): secrets redacted again, invisible / control characters removed."""
    return ticket_text.redact_secrets(_BAD_XML.sub("", str(text or "")))[0].strip()


STEP_NUMBER = re.compile(r"^\s*(?:step\s*)?\d{1,2}\s*[.):-]\s+", re.IGNORECASE)
STOP_WORDS = {"max_rounds": "after the retry round", "cost_cap": "the cost limit was reached",
              "time_cap": "the time limit was reached"}


def plain(reason):
    """A reason for a person: internal stop codes in words."""
    reason = safe(reason)
    for code, words in STOP_WORDS.items():
        reason = reason.replace(f"({code})", f"({words})")
    return reason


def usable(texts):
    """Safe, non-empty, de-duplicated (ignoring case) and without lines aimed at an AI."""
    out, seen = [], set()
    for t in texts:
        t = safe(t)
        if t and t.lower() not in seen and not ticket_text.instruction_lines(t):
            seen.add(t.lower())
            out.append(t)
    return out


# --- the document: blocks and inline parts --------------------------------------------------------------
# block:  ("h", level, text) | ("p", inline) | ("ul", [inline]) | ("ol", [inline]) | ("banner", tone, title, inline)
#         ("table", headers, rows)   row: [cell, ...] (cell = [block]) or ("span", inline) for a full-width row
#         ("expand", title, [block])
# inline: [part]   part: str | ("b", s) | ("i", s) | ("code", s) | ("a", text, url) | ("tag", tone, s)

def P(*parts):
    return ("p", [p for p in parts if p not in ("", None)])


def _esc(s):
    return _html.escape(_BAD_XML.sub("", str(s)), quote=True)


def _inline_x(parts, confluence):
    out = []
    for p in parts:
        if isinstance(p, str):
            out.append(_esc(p))
        elif p[0] == "b":
            out.append(f"<strong>{_esc(p[1])}</strong>")
        elif p[0] == "i":
            out.append(f"<em>{_esc(p[1])}</em>")
        elif p[0] == "code":
            out.append(f"<code>{_esc(p[1])}</code>")
        elif p[0] == "a":
            out.append(f'<a href="{_esc(p[2])}">{_esc(p[1])}</a>')
        elif p[0] == "tag" and confluence:
            colour = {"ok": "Green", "warn": "Yellow", "stop": "Red", "info": "Blue", "grey": "Grey"}[p[1]]
            out.append(f'<ac:structured-macro ac:name="status"><ac:parameter ac:name="colour">{colour}</ac:parameter>'
                       f'<ac:parameter ac:name="title">{_esc(p[2])}</ac:parameter></ac:structured-macro>')
        elif p[0] == "tag":
            out.append(f'<span class="tag {p[1]}">{_esc(p[2])}</span>')
    return "".join(out)


def _blocks_x(blocks, confluence):
    out = []
    for b in blocks:
        kind = b[0]
        if kind == "h":
            out.append(f"<h{b[1]}>{_esc(b[2])}</h{b[1]}>")
        elif kind == "p":
            out.append(f"<p>{_inline_x(b[1], confluence)}</p>")
        elif kind in ("ul", "ol"):
            items = "".join(f"<li>{_inline_x(i, confluence)}</li>" for i in b[1])
            out.append(f"<{kind}>{items}</{kind}>")
        elif kind == "banner":
            _, tone, title, inline = b
            body = f"<p>{_inline_x(inline, confluence)}</p>" if inline else ""
            if confluence:
                macro = {"ok": "tip", "warn": "note", "stop": "warning", "info": "info", "grey": "info"}[tone]
                out.append(f'<ac:structured-macro ac:name="{macro}"><ac:parameter ac:name="title">{_esc(title)}'
                           f"</ac:parameter><ac:rich-text-body>{body}</ac:rich-text-body></ac:structured-macro>")
            else:
                out.append(f'<div class="banner {tone}"><p><strong>{_esc(title)}</strong></p>{body}</div>')
        elif kind == "table":
            _, headers, rows = b
            head = "<tr>" + "".join(f"<th>{_esc(h)}</th>" for h in headers) + "</tr>"
            body = []
            for row in rows:
                if isinstance(row, tuple) and row[0] == "span":
                    body.append(f'<tr><td colspan="{len(headers)}">{_inline_x(row[1], confluence)}</td></tr>')
                else:
                    body.append("<tr>" + "".join(f"<td>{_blocks_x(cell, confluence)}</td>" for cell in row) + "</tr>")
            out.append(f"<table><tbody>{head}{''.join(body)}</tbody></table>")
        elif kind == "expand":
            _, title, inner = b
            if confluence:
                out.append(f'<ac:structured-macro ac:name="expand"><ac:parameter ac:name="title">{_esc(title)}'
                           f"</ac:parameter><ac:rich-text-body>{_blocks_x(inner, confluence)}</ac:rich-text-body>"
                           f"</ac:structured-macro>")
            else:
                out.append(f"<details><summary>{_esc(title)}</summary>{_blocks_x(inner, confluence)}</details>")
    return "".join(out)


_MD_SPECIAL = re.compile(r"([\\`*_\[\]<>|~#])")


def _md_esc(s):
    return _MD_SPECIAL.sub(r"\\\1", str(s).replace("&", "&amp;")).replace("\n", " ")


def _wrap_md(text, mark):
    """**bold** with any outer spaces moved outside the marks (CommonMark ignores `**x **`)."""
    t = str(text)
    core = t.strip()
    return t[:len(t) - len(t.lstrip())] + (f"{mark}{_md_esc(core)}{mark}" if core else "") + t[len(t.rstrip()):]


def _inline_md(parts):
    out = []
    for p in parts:
        if isinstance(p, str):
            out.append(_md_esc(p))
        elif p[0] == "b":
            out.append(_wrap_md(p[1], "**"))
        elif p[0] == "i":
            out.append(_wrap_md(p[1], "*"))
        elif p[0] == "code":
            out.append(f"`{str(p[1]).replace('`', chr(39))}`")
        elif p[0] == "a":
            out.append(f"[{_md_esc(p[1])}]({str(p[2]).replace(')', '%29').replace(' ', '%20')})")
        elif p[0] == "tag":
            out.append(f"**[{_md_esc(p[2])}]**")
    return "".join(out)


def _cell_md(cell):
    parts = []
    for b in cell:
        if b[0] == "p":
            parts.append(_inline_md(b[1]))
        elif b[0] == "ol":
            parts += [f"{n}. {_inline_md(i)}" for n, i in enumerate(b[1], 1)]
        elif b[0] == "ul":
            parts += [f"• {_inline_md(i)}" for i in b[1]]
    return "<br>".join(p for p in parts if p) or " "


def _blocks_md(blocks):
    out = []
    for b in blocks:
        kind = b[0]
        if kind == "h":
            out.append(f"{'#' * b[1]} {_md_esc(b[2])}")
        elif kind == "p":
            out.append(_inline_md(b[1]))
        elif kind == "ul":
            out.append("\n".join(f"- {_inline_md(i)}" for i in b[1]))
        elif kind == "ol":
            out.append("\n".join(f"{n}. {_inline_md(i)}" for n, i in enumerate(b[1], 1)))
        elif kind == "banner":
            _, tone, title, inline = b
            out.append(f"> **{_md_esc(title)}**" + (f"\n>\n> {_inline_md(inline)}" if inline else ""))
        elif kind == "table":
            _, headers, rows = b
            lines = ["| " + " | ".join(_md_esc(h) for h in headers) + " |", "|" + "---|" * len(headers)]
            for row in rows:
                if isinstance(row, tuple) and row[0] == "span":
                    lines.append("| " + _inline_md(row[1]) + " |" + " |" * (len(headers) - 1))
                else:
                    lines.append("| " + " | ".join(_cell_md(c) for c in row) + " |")
            out.append("\n".join(lines))
        elif kind == "expand":
            _, title, inner = b
            out.append(f"<details><summary>{_html.escape(title)}</summary>\n\n{_blocks_md(inner)}\n\n</details>")
    return "\n\n".join(o for o in out if o)


CSS = """
:root { --bg:#ffffff; --fg:#1d2125; --muted:#5e6c84; --line:#dfe1e6; --head:#f4f5f7;
        --ok:#e3fcef; --okfg:#006644; --warn:#fffae6; --warnfg:#974f0c; --stop:#ffebe6; --stopfg:#bf2600;
        --info:#deebff; --infofg:#0747a6; --grey:#f4f5f7; --greyfg:#42526e; }
@media (prefers-color-scheme: dark) { :root { --bg:#1d2125; --fg:#dee4ea; --muted:#9fadbc; --line:#38414a;
        --head:#22272b; --ok:#1c3329; --okfg:#7ee2b8; --warn:#3a2e14; --warnfg:#f5cd47; --stop:#42221f;
        --stopfg:#fd9891; --info:#1c2b41; --infofg:#85b8ff; --grey:#2c333a; --greyfg:#b6c2cf; } }
body { background:var(--bg); color:var(--fg); font:15px/1.5 system-ui, sans-serif; margin:0 auto;
       max-width:1200px; padding:16px; }
h1 { font-size:1.6em; } h2 { margin-top:1.8em; border-bottom:1px solid var(--line); } h3 { margin-top:1.4em; }
table { border-collapse:collapse; width:100%; margin:.6em 0; display:block; overflow-x:auto; }
th, td { border:1px solid var(--line); padding:6px 8px; vertical-align:top; text-align:left; }
th { background:var(--head); } td p, td ul, td ol { margin:.2em 0; } td ol, td ul { padding-left:1.3em; }
.banner { border-radius:6px; padding:8px 14px; margin:1em 0; }
.tag { border-radius:3px; padding:1px 6px; font-size:.75em; font-weight:700; white-space:nowrap; }
.ok { background:var(--ok); color:var(--okfg); } .warn { background:var(--warn); color:var(--warnfg); }
.stop { background:var(--stop); color:var(--stopfg); } .info { background:var(--info); color:var(--infofg); }
.grey { background:var(--grey); color:var(--greyfg); }
.banner p { color:var(--fg); } .banner p:first-child { color:inherit; }
details { margin:.8em 0; } summary { cursor:pointer; font-weight:600; }
code { font-size:.9em; } a { color:var(--infofg); }
"""


def to_storage(blocks):
    return _blocks_x(blocks, confluence=True)


def to_html(title, blocks):
    return (f'<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
            f'<meta name="viewport" content="width=device-width, initial-scale=1">\n<title>{_esc(title)}</title>\n'
            f"<style>{CSS}</style>\n</head>\n<body>\n<h1>{_esc(title)}</h1>\n{_blocks_x(blocks, confluence=False)}\n"
            f"</body>\n</html>\n")


def to_markdown(title, blocks):
    return f"# {_md_esc(title)}\n\n{_blocks_md(blocks)}\n"


# --- facts from the state ---------------------------------------------------------------------------------

def _snapshots():
    try:
        return json.loads(SNAPSHOTS.read_text(encoding="utf-8")).get("repos", {})
    except (OSError, ValueError):
        return {}


def code_link(snapshots, repo, path, lines):
    """GitHub link to the cited lines at the frozen commit, or None for an unknown repo."""
    snap = snapshots.get(repo) or {}
    url, commit = snap.get("url", ""), snap.get("commit", "")
    if not (url.startswith("https://github.com/") and re.fullmatch(r"[0-9a-f]{7,40}", commit or "")):
        return None
    base = url[:-4] if url.endswith(".git") else url
    a, b = (list(lines) + [0, 0])[:2]
    return f"{base}/blob/{commit}/{path}" + (f"#L{a}-L{b}" if a and b else "")


def _collect(state, keys):
    """Every string value stored under one of `keys` anywhere in the state (sorted, unique)."""
    found = set()

    def walk(x):
        if isinstance(x, dict):
            for k, v in x.items():
                if k in keys and isinstance(v, str) and v:
                    found.add(v)
                else:
                    walk(v)
        elif isinstance(x, list):
            for v in x:
                walk(v)
    walk({k: state.get(k) for k in ("understanding", "orchestration", "results", "plan", "review")})
    return sorted(found)


def verdict_of(row, review):
    per = (review or {}).get("per_criterion", {}).get(row["id"])
    if per:
        return per["verdict"], per
    return row.get("status", "covered"), {}


def _ticket_line(ticket):
    key, url = safe(ticket.get("key", "")) or "the ticket", str(ticket.get("url") or "")
    return ("a", key, url) if url.startswith("https://") else ("b", key)


def _status_banner(status, state):
    review, orch = state.get("review") or {}, state.get("orchestration") or {}
    reason = plain((review.get("final") or {}).get("reason", "") or orch.get("stopped", ""))
    if status == "complete":
        return ("banner", "ok", "Ready for PM review", ["Every acceptance criterion passed the review."])
    if status == "needs-clarification":
        return ("banner", "stop", "Needs clarification: no UAT test cases yet",
                [safe((state.get("clarification") or {}).get("headline", ""))])
    return ("banner", "warn", "Needs attention", [reason or "The run did not finish every criterion."])


def _draft_note(ticket, cases=True):
    return P("Draft written by SpecBridge from the code at the frozen version, for ", _ticket_line(ticket),
             ". Please review it before use." + (" The Actual result and Pass/Fail columns are for the tester."
                                                  if cases else ""))


def _screens_table(screens):
    rows = []
    for s in screens:
        where = s.get("where") or ([s["matches"]] if s.get("matches") else [])
        rows.append([[P(safe(s.get("name", "")))],
                     [P("new" if s.get("status") == "new" else "existing")],
                     [P(safe(s.get("role", "")) or "-")],
                     [P(", ".join(safe(w) for w in where) or "-")]])
    return ("table", ["Screen", "New or existing", "Changed or used", "Where in the code"], rows) if rows else \
        P(("i", "No screens were named."))


def _case_rows(case, evidence_ids, criteria_label=None):
    ev = [e if e in evidence_ids else f"{e} (not found)" for e in case.get("evidence_ids", [])]
    first = [P(("b", safe(case["id"])), f" · {TYPE_NAME.get(case.get('type'), safe(case.get('type', '')))}"),
             P(safe(case.get("title", "")))]
    if criteria_label:
        first.append(P(("i", criteria_label)))
    first.append(P(("i", "Code: " + (", ".join(ev) or "none cited"))))
    pre = usable(case.get("preconditions", []))
    row = [first,
           [("ul", [[p] for p in pre])] if pre else [P("-")],
           [("ol", [[STEP_NUMBER.sub("", safe(s))] for s in case.get("steps", []) if STEP_NUMBER.sub("", safe(s))])],
           [P(safe(case.get("expected", "")))],
           [], []]
    rows = [row]
    flags = case.get("flags") or []
    if flags:
        parts = [("b", "⚠ May be ambiguous, please check: ")]
        parts.append("; ".join(f"{safe(f.get('detail', ''))} ({safe(f.get('kind', ''))})" for f in flags))
        rows.append(("span", parts))
    return rows


# --- the three kinds of page ------------------------------------------------------------------------------

def test_plan_blocks(state, status, snapshots):
    ticket, u = state.get("ticket") or {}, state.get("understanding") or {}
    plan, review = state["plan"], state.get("review") or {}
    cases = plan.get("cases", [])
    by_id = {c["id"]: c for c in cases}
    evidence_ids = {e["id"] for e in plan.get("evidence", [])}
    quotes = {c.get("id"): safe(c.get("quote", "")) for c in u.get("criteria", [])}
    b = [_status_banner(status, state), _draft_note(ticket)]

    b += [("h", 2, "1. Summary"), P(("b", "What the ticket asks: "), safe(u.get("intent", "")) or "-"),
          P(("b", "Test scope: "), SCOPE_TEXT.get(u.get("test_scope", "full"), safe(u.get("test_scope", "")))),
          ("h", 3, "Affected screens"), _screens_table(u.get("screens", []))]
    reg = usable(u.get("regression_screens", []))
    if reg:
        b += [P(("b", "Screens to check for regressions: "), ", ".join(reg))]

    common = usable(plan.get("common_preconditions", []))
    b += [("h", 2, "2. Before you start"), ("ul", [[c] for c in common]) if common else P("No shared preconditions.")]

    b += [("h", 2, "3. Test cases by acceptance criterion")]
    placed = set()
    for row in plan.get("criteria", []):
        verdict, per = verdict_of(row, review)
        tone, label = VERDICT_TAG.get(verdict, ("grey", verdict.upper()))
        if row.get("status") == "regression" and verdict == "ok":
            tone, label = "ok", "OK · REGRESSION CHECK"
        b.append(("h", 3, f"{safe(row['id'])}: {safe(row.get('text', ''))}"))
        b.append(P(("tag", tone, label)))
        if quotes.get(row["id"]):
            b.append(P(("i", f"Ticket: “{quotes[row['id']]}”")))
        if verdict == "weak":
            problems = [[f"{safe(p.get('case')) or 'Criterion'} ({safe(p.get('kind', ''))}): {safe(p.get('detail', ''))}"]
                        for p in per.get("problems", [])]
            b.append(("banner", "warn", "May be ambiguous, please check",
                      [f"The reviewer found problems{' ' if problems else ''}"
                       f"{'below' if problems else 'with this criterion'}."]))
            if problems:
                b.append(("ul", problems))
            if per.get("retry_hint"):
                b.append(P(("b", "What is missing: "), safe(per["retry_hint"])))
        if per.get("ai") == "not reviewed by the AI" and verdict in ("ok", "weak"):
            b.append(P(("i", "Checked by the code checks only: the AI review of this criterion failed.")))
        if verdict in ("untestable", "skipped", "uncovered", "failed"):
            b.append(P(("b", "Why there are no test cases: "),
                       safe(per.get("reason") or row.get("detail", "")) or "no reason was given"))
        own = [by_id[c] for c in row.get("cases", []) if c in by_id and by_id[c].get("type") != "e2e"
               and by_id[c]["criterion_ids"][:1] == [row["id"]]]
        if own:
            b.append(("table", CASE_HEADERS, [r for c in own for r in _case_rows(c, evidence_ids)]))
            placed |= {c["id"] for c in own}
        shared = [c for c in cases if c.get("type") != "e2e" and row["id"] in c["criterion_ids"]
                  and c["criterion_ids"][:1] != [row["id"]]]
        flows = [c for c in cases if c.get("type") == "e2e" and row["id"] in c["criterion_ids"]]
        if shared:
            b.append(P("Also covered by ", ", ".join(f"{safe(c['id'])} (under {safe(c['criterion_ids'][0])})"
                                                     for c in shared), "."))
        if flows:
            b.append(P("Also tested in end-to-end flow ", ", ".join(safe(c["id"]) for c in flows), "."))

    flows = [c for c in cases if c.get("type") == "e2e"]
    if flows:
        b += [("h", 2, "4. End-to-end flows"),
              ("table", CASE_HEADERS, [r for c in flows for r in
                                       _case_rows(c, evidence_ids, "Covers " + " → ".join(c["criterion_ids"]))])]
        placed |= {c["id"] for c in flows}
    rest = [c for c in cases if c["id"] not in placed]
    if rest:
        b += [("h", 3, "Other test cases"), ("table", CASE_HEADERS, [r for c in rest for r in _case_rows(c, evidence_ids)])]

    questions = usable([*u.get("questions", []), *plan.get("questions", [])])
    b += [("h", 2, "5. Open questions for the PM"), ("ol", [[q] for q in questions]) if questions else P("None.")]

    notes = usable(plan.get("notes", []))
    missing = usable(r.get("missing", "") for r in state.get("results") or [])
    if notes or missing:
        inner = []
        if notes:
            inner += [P("What the writers noticed in the code:"), ("ul", [[n] for n in notes])]
        if missing:
            inner += [P("What the writers could not find:"), ("ul", [[m] for m in missing])]
        b += [("h", 2, "6. Notes from the code"), ("expand", "Show the notes", inner)]

    b += review_blocks(plan, review)
    b += evidence_blocks(plan, snapshots)
    return b


def review_blocks(plan, review):
    if not review:
        return [("h", 2, "7. Review report"), P(("i", "No review was made."))]
    sc, final = review.get("scores") or {}, review.get("final") or {}
    grounded = sc.get("grounded_cases")
    b = [("h", 2, "7. Review report"),
         P(("b", "Criteria ok: "), str(sc.get("criteria_ok", "-")), " · ", ("b", "Cases fully grounded: "),
           f"{round(grounded * 100)}%" if isinstance(grounded, (int, float)) else "-", " · ", ("b", "Review rounds: "),
           str(review.get("round", 1)))]
    if final.get("reason"):
        b.append(P(("b", "Final: "), plain(final["reason"])))
    rows = []
    for row in plan.get("criteria", []):
        verdict, per = verdict_of(row, review)
        tone, label = VERDICT_TAG.get(verdict, ("grey", verdict.upper()))
        how = {"reviewed": "AI and code checks", "not reviewed by the AI": "code checks only"}.get(per.get("ai"), "-")
        rows.append([[P(safe(row["id"]))], [P(("tag", tone, label))], [P(str(len(per.get("problems", []))))], [P(how)]])
    b.append(("table", ["Criterion", "Verdict", "Problems", "Checked by"], rows))
    changes = [c for c in plan.get("changes", []) if isinstance(c, dict) and c.get("applied", True)]
    if changes:
        b.append(("expand", "Changes made when the results were merged",
                  [("ul", [[safe(c.get("change", "")) + (f" ({safe(c['why'])})" if c.get("why") else "")]
                           for c in changes])]))
    return b


def evidence_blocks(plan, snapshots):
    rows = []
    for e in plan.get("evidence", []):
        a, z = (list(e.get("lines") or []) + [0, 0])[:2]
        link = code_link(snapshots, e.get("repo", ""), e.get("path", ""), e.get("lines") or [])
        rows.append([[P(("b", safe(e["id"])))], [P(("code", f"{safe(e.get('repo', ''))}/{safe(e.get('path', ''))}"))],
                     [P(f"{a}-{z}" if a else "-")], [P(("a", "view at the frozen version", link) if link else "-")]])
    return [("h", 2, "8. Code the test cases cite"),
            ("table", ["ID", "File", "Lines", "Link"], rows) if rows else P("No code was cited.")]


def run_blocks(state, settings, now, snapshots, heading="Run details"):
    spent = state.get("spent") or {}
    started = state.get("started_at")
    results = state.get("results") or []
    items = [P(("b", "Run: "), ("code", safe(state.get("run_id", "-"))), f" · mode {safe(state.get('mode', '-'))}")]
    if isinstance(started, (int, float)):
        when = time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime(started))
        items.append(P(("b", "Started: "), when, f" · about {max(0.0, (now - started) / 60):.1f} min to this page"))
    items.append(P(("b", "Cost: "), f"${spent.get('cost', 0):.3f} (estimated from list prices)",
                   f" · {int(spent.get('tokens', 0)):,} tokens"))
    items.append(P(("b", "Rounds: "), str(state.get("round", 0)), " · ", ("b", "Worker runs: "), str(len(results))))
    models = _collect(state, {"model", "agent_model", "writer_model"}) + _collect(state, {"models"})
    prompts = _collect(state, {"prompt_version", "agent_prompt", "cases_prompt"})
    items.append(P(("b", "Models: "), ", ".join(dict.fromkeys(safe(m) for m in models)) or "-"))
    items.append(P(("b", "Prompts: "), ", ".join(safe(p) for p in prompts) + f", {VERSION}"))
    if settings is not None:
        items.append(P(("b", "Limits: "), f"${settings.cost_cap_usd} per ticket, {settings.max_rounds} rounds, "
                                         f"{settings.max_tool_calls_per_round} tool calls per worker"))
    frozen = ", ".join(f"{name} @ {str(s.get('commit', ''))[:8]}" for name, s in sorted(snapshots.items()))
    items.append(P(("b", "Code version (frozen): "), frozen or "-"))
    return [("h", 2, heading), ("expand", "Show the run details", items)]


def clarification_blocks(state, status):
    ticket, c = state.get("ticket") or {}, state.get("clarification") or {}
    und = c.get("understood") or {}
    b = [_status_banner(status, state), _draft_note(ticket, cases=False),
         ("h", 2, "Why there are no test cases yet"), P(safe(c.get("reason", "")) or "-"),
         ("h", 2, "What SpecBridge understood"), P(("b", "Intent: "), safe(und.get("intent", "")) or "-")]
    crit = [[("b", safe(x.get("id", ""))), f": {safe(x.get('text', ''))}"] for x in und.get("criteria", [])]
    b.append(("ul", crit) if crit else P(("i", "No acceptance criteria were found.")))
    b += [("h", 3, "Screens"), _screens_table(und.get("screens", []))]
    risks = [[f"{safe(r.get('kind', ''))}: {safe(r.get('detail', ''))}"] for r in c.get("risks", [])]
    if risks:
        b += [("h", 3, "Risks"), ("ul", risks)]
    questions = usable(c.get("questions", []))
    b += [("h", 2, "Questions for the PM"), ("ol", [[q] for q in questions]) if questions else P("None."),
          ("h", 2, "Next step"), P(safe(c.get("next_step", "")) or "-")]
    return b


def no_plan_blocks(state, status):
    ticket, u = state.get("ticket") or {}, state.get("understanding") or {}
    b = [_status_banner(status, state), _draft_note(ticket, cases=False),
         P("The run stopped before any test cases were written."),
         ("h", 2, "What SpecBridge understood"), P(("b", "Intent: "), safe(u.get("intent", "")) or "-")]
    crit = [[("b", safe(x.get("id", ""))), f": {safe(x.get('text', ''))}"] for x in u.get("criteria", [])]
    if crit:
        b.append(("ul", crit))
    b += [("h", 3, "Screens"), _screens_table(u.get("screens", []))]
    questions = usable(u.get("questions", []))
    if questions:
        b += [("h", 2, "Open questions for the PM"), ("ol", [[q] for q in questions])]
    return b


# --- the comment and the summary --------------------------------------------------------------------------

def _cut(text, n):
    return text if len(text) <= n else text[:n - 1].rstrip() + "…"


def summary_of(state, status, kind):
    plan, review = state.get("plan") or {}, state.get("review") or {}
    verdicts = {}
    for row in plan.get("criteria", []):
        v, _ = verdict_of(row, review)
        verdicts.setdefault(v, []).append(row["id"])
    cases = plan.get("cases", [])
    questions = usable([*(state.get("understanding") or {}).get("questions", []), *plan.get("questions", [])]) \
        if kind == "test-plan" else usable((state.get("clarification") or {}).get("questions", []))
    return {"kind": kind, "status": status, "criteria": {k: len(v) for k, v in verdicts.items()},
            "weak": verdicts.get("weak", []), "cases": len(cases),
            "flows": sum(1 for c in cases if c.get("type") == "e2e"),
            "flagged_cases": sum(1 for c in cases if c.get("flags")), "questions": len(questions)}


def comment_for(state, key, status, summary):
    if summary["kind"] == "clarification" and (state.get("clarification") or {}).get("comment"):
        return safe(state["clarification"]["comment"])[:MAX_COMMENT_CHARS]
    if summary["kind"] == "no-plan":
        reason = safe((state.get("orchestration") or {}).get("stopped", "")) or "the run stopped early"
        lines = [f"{COMMENT_MARKER} {key}: incomplete - no UAT test cases yet", _cut(f"Reason: {reason}.", 600)]
    else:
        crit, weak = summary["criteria"], summary["weak"]
        head = "UAT test cases ready for PM review" if status == "complete" else \
            "UAT test cases drafted - some need attention"
        counts = [f"{crit.get('ok', 0)} ok"]
        if weak:
            counts.append(_cut(f"{len(weak)} {'needs' if len(weak) == 1 else 'need'} attention: {', '.join(weak)}", 300))
        counts += [f"{crit[k]} {k}" for k in ("untestable", "skipped", "uncovered", "failed") if crit.get(k)]
        total = sum(crit.values())
        lines = [f"{COMMENT_MARKER} {key}: {head}",
                 f"{summary['cases']} test cases for {total} acceptance criteria ({'; '.join(counts)})."]
        extra = []
        if summary["flagged_cases"]:
            n = summary["flagged_cases"]
            extra.append(f"{n} {'case is' if n == 1 else 'cases are'} flagged \"may be ambiguous\".")
        if summary["questions"]:
            n = summary["questions"]
            extra.append(f"{n} open {'question' if n == 1 else 'questions'}.")
        if extra:
            lines.append(" ".join(extra))
    lines.append(f"Page: {PAGE_LINK}")
    return _cut("\n".join(lines), MAX_COMMENT_CHARS)


# --- the node ---------------------------------------------------------------------------------------------

def render_page(state, settings=None, now=None):
    """The page for any finished state. `now` (seconds) only feeds the 'time to this page' line."""
    now = time.time() if now is None else now
    status = state.get("status") or "incomplete"
    ticket = state.get("ticket") or {}
    key = safe(ticket.get("key", "")) or "UNKNOWN"
    snapshots = _snapshots()
    if status == "needs-clarification" and state.get("clarification"):
        kind, blocks = "clarification", clarification_blocks(state, status)
    elif (state.get("plan") or {}).get("criteria"):
        kind, blocks = "test-plan", test_plan_blocks(state, status, snapshots)
    else:
        kind, blocks = "no-plan", no_plan_blocks(state, status)
    blocks += run_blocks(state, settings, now, snapshots, "9. Run details" if kind == "test-plan" else "Run details")
    title = _cut(f"UAT {key}: {safe(ticket.get('title', '')) or 'untitled ticket'}", MAX_TITLE)
    summary = summary_of(state, status, kind)
    labels = [LABEL_OK.sub("-", key.lower()).strip("-") or "unknown", "specbridge", "awaiting-pm-review"]
    return {"title": title, "labels": labels, "storage": to_storage(blocks), "html": to_html(title, blocks),
            "markdown": to_markdown(title, blocks), "comment": comment_for(state, key, status, summary),
            "summary": summary, "version": VERSION}


def make_node(clock=time.time):
    def node(state, settings):
        return {"page": render_page(state, settings, clock())}
    return node


node = make_node()
