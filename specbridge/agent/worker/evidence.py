"""A worker's evidence: exactly the code it read, so every test case can cite it (ARCHITECTURE.md D7).

Evidence is a plain list of dicts (it lives in the worker's checkpointed state):
  {id: "E1", kind: "read" | "grep", repo, path, lines: [start, end], text, why}
Only code the worker actually received counts: lines of a read_file and grep match lines; search results and
usage lists are pointers, not evidence. `compact` keeps the worker's conversation small (D8): when it nears the
cap, older tool results are cut to their first line, which names the evidence ids, so the worker can re-read.
"""
MAX_EXCERPT = 600
KEEP_FULL = 2            # newest tool results kept whole
COMPACT_AT = 0.7         # share of the cap at which compaction starts
TOOL_HEADER = "TOOL RESULT"


def add(evidence, kind, repo, path, start, end, text, why=""):
    """The id of this evidence, added if new (the same file and lines read twice get one id)."""
    for e in evidence:
        if (e["repo"], e["path"], e["lines"]) == (repo, path, [start, end]):
            return e["id"]
    eid = f"E{len(evidence) + 1}"
    evidence.append({"id": eid, "kind": kind, "repo": repo, "path": path, "lines": [start, end],
                     "text": text, "why": why})
    return eid


def ids(evidence):
    return {e["id"] for e in evidence}


def pointer(e):
    """What leaves the worker: where the evidence is, plus a short excerpt, not the whole code."""
    text = e["text"] if len(e["text"]) <= MAX_EXCERPT else e["text"][:MAX_EXCERPT] + "\n..."
    return {"id": e["id"], "kind": e["kind"], "repo": e["repo"], "path": e["path"], "lines": e["lines"],
            "why": e.get("why", ""), "excerpt": text}


def tokens(messages):
    return sum(len(m["content"]) for m in messages) // 4


def compact(messages, cap_tokens):
    """Messages with older tool results cut to their header line once the conversation passes COMPACT_AT * cap.
    Returns (messages, how many were compacted)."""
    if tokens(messages) <= cap_tokens * COMPACT_AT:
        return messages, 0
    tool_positions = [i for i, m in enumerate(messages) if m["role"] == "user" and m["content"].startswith(TOOL_HEADER)]
    out, done = [dict(m) for m in messages], 0
    for i in tool_positions[:-KEEP_FULL]:
        first = out[i]["content"].split("\n", 1)[0]
        if "[compacted" not in first:
            out[i]["content"] = first + " [compacted: the details were removed to save space; read again if needed]"
            done += 1
        if tokens(out) <= cap_tokens * COMPACT_AT:
            break
    return out, done
