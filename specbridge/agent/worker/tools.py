"""The worker's tool runner: check the arguments, call the code source, check the answer's shape, turn it into
a short text for the AI (marked as data, D3) and record what was read as evidence.

The argument schemas come from code_tools.TOOLS; the answers are checked here too (the TODO in code_tools.py).
"""
import json

from specbridge.agent.worker import evidence as ev
from specbridge.brain import schema_errors
from specbridge.code_tools import TOOLS

NAMES = [t["name"] for t in TOOLS]
ARGS = {t["name"]: {**t["input_schema"], "additionalProperties": False} for t in TOOLS}
OUTPUT_KEYS = {"search_code": {"results"}, "read_file": {"repo", "path", "start_line", "end_line", "text"},
               "grep": {"matches"}, "find_usages": {"links"}}
MAX_READ_CHARS = 12_000      # about 3k tokens of code per read
MAX_GREP = 15
MAX_LINKS = 30
MAX_SEARCH = 10


def parse_args(raw):
    """The action's args: a JSON object (or a JSON string of one, as the model sends it)."""
    if isinstance(raw, dict):
        return raw, None
    try:
        value = json.loads(raw or "{}")
    except (TypeError, ValueError) as err:
        return None, f"args are not valid JSON: {err}"
    return (value, None) if isinstance(value, dict) else (None, "args must be a JSON object")


def run(source, name, args, evidence, why=""):
    """(text for the AI, new evidence ids). Never raises: problems come back as a TOOL ERROR the AI can react to."""
    if name not in NAMES:
        return f"TOOL ERROR: unknown tool {name!r}; use one of {', '.join(NAMES)} or done", []
    problems = schema_errors(args, ARGS[name])
    if problems:
        return f"TOOL ERROR: bad arguments for {name}: {'; '.join(problems[:3])}", []
    try:
        result = source.call(name, args)
    except Exception as err:  # noqa: BLE001 - a broken tool call is the AI's problem to work around, not a crash
        return f"TOOL ERROR: {name} failed: {type(err).__name__}: {str(err)[:200]}", []
    if not isinstance(result, dict):
        return f"TOOL ERROR: {name} gave an unexpected answer", []
    if "error" in result:
        return f"TOOL ERROR: {result['error']}", []
    missing = OUTPUT_KEYS[name] - set(result)
    if missing:
        return f"TOOL ERROR: {name} answer is missing {sorted(missing)}", []
    return globals()[f"_{name}"](result, args, evidence, why)


def _search_code(result, args, evidence, why):
    lines = [f"{ev.TOOL_HEADER} search_code {json.dumps(args.get('query', ''))[:120]}: "
             f"{len(result['results'])} file(s) (pointers only; read a file to use it as evidence)"]
    for r in result["results"][:MAX_SEARCH]:
        where = "; ".join(r.get("appears_in") or [])[:150]
        lines.append(f"- {r['repo']}/{r['path']} [{r.get('piece') or '-'}, lines {r.get('lines')}]"
                     + (f" appears in: {where}" if where else ""))
    return "\n".join(lines), []


def _read_file(result, args, evidence, why):
    code_lines = result["text"].split("\n")
    shown, size = [], 0
    for line in code_lines:
        if size + len(line) > MAX_READ_CHARS and shown:
            break
        shown.append(line)
        size += len(line) + 1
    start = result["start_line"]
    end = start + len(shown) - 1
    eid = ev.add(evidence, "read", result["repo"], result["path"], start, end, "\n".join(shown), why)
    more = f"; the file has {result.get('total_lines', '?')} lines" + \
        (f"; cut at line {end}, read from {end + 1} to see more" if end < result["end_line"] else "")
    header = f"{ev.TOOL_HEADER} read_file -> {eid} = {result['repo']}/{result['path']} lines {start}-{end}{more}"
    return header + "\n<code>\n" + "\n".join(shown) + "\n</code>", [eid]


def _grep(result, args, evidence, why):
    matches = result["matches"][:MAX_GREP]
    new = []
    lines = [f"{ev.TOOL_HEADER} grep {json.dumps(args.get('pattern', ''))[:80]}: {len(result['matches'])} match(es)"
             + (" (more not shown)" if result.get("truncated") or len(result["matches"]) > MAX_GREP else "")]
    for m in matches:
        eid = ev.add(evidence, "grep", m["repo"], m["path"], m["line"], m["line"], m["text"], why)
        new.append(eid)
        lines.append(f"- {eid} {m['repo']}/{m['path']}:{m['line']}: {m['text']}")
    lines[0] += f" -> {', '.join(new)}" if new else ""
    return "\n".join(lines), new


def _find_usages(result, args, evidence, why):
    links = result["links"][:MAX_LINKS]
    lines = [f"{ev.TOOL_HEADER} find_usages {args.get('repo')}/{args.get('path')}: {len(result['links'])} link(s)"]
    lines += [f"- {l['direction']} {l['repo']}/{l['path']} ({l['kind']}{', via ' + str(l['via']) if l.get('via') else ''})"
              for l in links]
    return "\n".join(lines), []
