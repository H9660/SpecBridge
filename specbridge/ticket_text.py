"""Turn a Jira ticket into clean, safe plain text (used by the intake node).

- `adf_to_text`: Jira rich text (ADF) -> plain text that keeps the structure the AI needs: headings,
  paragraphs, numbered / bulleted lists (one criterion per line), code blocks, tables row by row.
  Images are dropped, @mentions become "(someone)", links keep their text but not their target.
- `redact_secrets`: passwords, API keys, tokens and private keys -> <redacted-secret>.
- `instruction_lines`: lines that talk to the AI ("ignore your previous rules", "note for the AI", ...).
  They are only reported; the text stays, and understand reports it as a risk (ARCHITECTURE.md D3).
"""
import re

REDACTED = "<redacted-secret>"
DROPPED = {"media", "mediaSingle", "mediaGroup", "mediaInline"}
FILE_NAME = re.compile(r"[\w\-/]+\.(?:tsx?|jsx?|scss)\b")


# --- rich text -> plain text ------------------------------------------------------------------------

def adf_to_text(doc):
    """(text, counts) where counts = {attachments, mentions, links, unknown}."""
    counts = {"attachments": 0, "mentions": 0, "links": 0, "unknown": 0}
    if not doc:
        return "", counts
    blocks = doc.get("content", []) if isinstance(doc, dict) and doc.get("type") == "doc" else doc
    text = _join_blocks(blocks if isinstance(blocks, list) else [blocks], counts)
    return re.sub(r"\n{3,}", "\n\n", text).strip(), counts


def _join_blocks(nodes, counts, indent=""):
    parts = [p for p in (_block(n, counts, indent) for n in nodes) if p.strip()]
    return "\n\n".join(parts)


def _block(node, counts, indent=""):
    kind = node.get("type")
    content = node.get("content", [])
    if kind in DROPPED:
        counts["attachments"] += 1
        return ""
    if kind == "paragraph":
        return indent + _inline(content, counts).replace("\n", "\n" + indent)
    if kind == "heading":
        return indent + "#" * node.get("attrs", {}).get("level", 1) + " " + _inline(content, counts)
    if kind in ("bulletList", "orderedList"):
        start = node.get("attrs", {}).get("order", 1) if kind == "orderedList" else None
        lines = []
        for i, item in enumerate(content):
            marker = f"{start + i}. " if start is not None else "- "
            lines.append(_list_item(item, counts, indent, marker))
        return "\n".join(lines)
    if kind == "codeBlock":
        code = "".join(t.get("text", "") for t in content)
        return "\n".join(indent + line for line in ["```", *code.split("\n"), "```"])
    if kind == "blockquote":
        inner = _join_blocks(content, counts)
        return "\n".join(indent + "> " + line for line in inner.split("\n"))
    if kind == "rule":
        return indent + "---"
    if kind == "table":
        rows = []
        for row in content:
            cells = [_join_blocks(c.get("content", []), counts).replace("\n", " ") for c in row.get("content", [])]
            rows.append(indent + "| " + " | ".join(cells) + " |")
        return "\n".join(rows)
    if kind in ("panel", "expand", "nestedExpand", "layoutSection", "layoutColumn", "doc"):
        title = node.get("attrs", {}).get("title")
        inner = _join_blocks(content, counts, indent)
        return (indent + title + "\n" + inner) if title else inner
    if kind == "blockCard":
        counts["links"] += 1
        return indent + "[link]"
    # anything else: keep its text, never fail on an unknown element
    counts["unknown"] += 1
    if content:
        return _join_blocks(content, counts, indent) if any(c.get("content") for c in content) \
            else indent + _inline(content, counts)
    return indent + node.get("text", "")


def _list_item(item, counts, indent, marker):
    pad = indent + " " * len(marker)
    parts = []
    for i, child in enumerate(item.get("content", [])):
        if child.get("type") in ("bulletList", "orderedList"):
            parts.append(_block(child, counts, indent + "  "))
        else:
            text = _block(child, counts, "")
            parts.append((indent + marker if not parts else pad) + text.replace("\n", "\n" + pad))
    return "\n".join(parts) if parts else indent + marker.rstrip()


def _inline(nodes, counts):
    out = []
    for n in nodes:
        kind = n.get("type")
        if kind == "text":
            text = n.get("text", "")
            marks = {m.get("type") for m in n.get("marks") or []}
            if "link" in marks:
                counts["links"] += 1
            out.append(f"`{text}`" if "code" in marks else text)
        elif kind == "hardBreak":
            out.append("\n")
        elif kind == "mention":
            counts["mentions"] += 1
            out.append("(someone)")
        elif kind == "inlineCard":
            counts["links"] += 1
            out.append("[link]")
        elif kind == "emoji":
            out.append(n.get("attrs", {}).get("text") or n.get("attrs", {}).get("shortName", ""))
        elif kind in ("status", "date"):
            attrs = n.get("attrs", {})
            out.append(attrs.get("text") or str(attrs.get("timestamp", "")))
        elif kind in DROPPED:
            counts["attachments"] += 1
        else:
            counts["unknown"] += 1
            out.append(_inline(n.get("content", []), counts) if n.get("content") else n.get("text", ""))
    return "".join(out)


# --- secrets ----------------------------------------------------------------------------------------

SECRET_PATTERNS = [
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}"),            # JWT
    re.compile(r"\bsk-(?:[a-z]+-){0,3}[A-Za-z0-9_-]{16,}"),                                  # OpenAI / OpenRouter / Stripe style
    re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})"),            # GitHub
    re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b"),                                            # AWS access key id
    re.compile(r"\bATATT[A-Za-z0-9_\-=]{20,}"),                                              # Atlassian API token
    re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b"),                                                # Google API key
    re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}"),                                           # Slack
    re.compile(r"(?<=\bBearer )[A-Za-z0-9._~+/=-]{16,}"),
]
# "password Rooks@Secret2026!", "api key: abc123...": the value is redacted only if it looks like a secret,
# so "the password field is cleared" and "password is incorrect" are left alone.
SECRET_AFTER_WORD = re.compile(
    r"\b(pass(?:word|wd|code|phrase)?|pwd|secret|token|api[ _-]?key|access[ _-]?key|client[ _-]?secret)"
    r"(\s*(?:is\s+|:\s*|=\s*|\s+))(\S+)", re.I)


def _looks_secret(value):
    v = value.rstrip(".,;)'\"")
    if len(v) < 6 or v == REDACTED:
        return False
    has_letter, has_digit = re.search(r"[A-Za-z]", v), re.search(r"\d", v)
    has_symbol = re.search(r"[^A-Za-z0-9]", v)
    return bool(has_letter and (has_digit or has_symbol))


def redact_secrets(text):
    """(text, how many secrets were replaced)."""
    count = 0
    for pattern in SECRET_PATTERNS:
        text, n = pattern.subn(REDACTED, text)
        count += n

    def value(m):
        nonlocal count
        if not _looks_secret(m.group(3)):
            return m.group(0)
        count += 1
        tail = m.group(3)[len(m.group(3).rstrip(".,;)'\"")):]
        return m.group(1) + m.group(2) + REDACTED + tail
    text = SECRET_AFTER_WORD.sub(value, text)
    return text, count


# --- text aimed at the AI ---------------------------------------------------------------------------

AI = r"(?:ai|a\.i\.|assistant|bot|llm|model|agent|chatgpt|gpt|claude|gemini|copilot|automation|tool)"
INSTRUCTION_PATTERNS = [
    re.compile(r"\b(?:ignore|disregard|forget|override)\b[^.\n]{0,40}\b(?:rules|instructions|prompts?|guidelines|"
               r"directions|guardrails|policies)\b", re.I),
    re.compile(rf"\b(?:note|message|instructions?|reminder)\s+(?:for|to)\s+(?:the\s+|any\s+)?{AI}\b", re.I),
    re.compile(rf"\b(?:dear|hey|attention)\s+{AI}\b", re.I),
    re.compile(r"\byou are now\b|\bfrom now on,? you\b|\bsystem prompt\b|\bjailbreak\b", re.I),
    re.compile(r"\bdo not (?:write|create|generate|produce|add) (?:any )?test cases\b", re.I),
    re.compile(r"\b(?:mark|set|flag|label)\b[^.\n]{0,40}\bas (?:approved|signed[ -]off)\b", re.I),
    re.compile(r"\b(?:qa|uat|pm) sign-?off\b|\bapproved by the pm\b", re.I),
    re.compile(r"\b(?:reveal|print|output|send|share|leak|include)\b[^.\n]{0,30}\b(?:your system prompt|"
               r"your instructions|api keys?|credentials|secrets|access tokens?|the admin password|your password)\b", re.I),
]


def instruction_lines(text):
    """Line numbers (1-based) of lines that look like instructions to the AI."""
    return [i for i, line in enumerate(text.split("\n"), 1) if any(p.search(line) for p in INSTRUCTION_PATTERNS)]


def file_names(text):
    return sorted(set(FILE_NAME.findall(text)))
