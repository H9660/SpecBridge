"""Turn a Jira ticket field into clean, safe plain text (used by the intake node).

- `adf_to_text`: Jira rich text (ADF, a JSON string of ADF, HTML or plain text) -> plain text that keeps the
  structure the AI needs: headings, paragraphs, numbered / bulleted / checklist items (one criterion per
  line), code blocks, tables row by row, struck-out (removed) text. Images become "[image: alt text]" when
  they have alt text, @mentions become "(someone)", links keep their text but not their target (Jira keys
  and host names of cards are kept). Never raises: a malformed node is skipped and counted.
- `clean_text`: strips invisible / control characters and decodes hidden "tag character" payloads.
- `redact_secrets`: passwords, API keys, tokens, private keys, credentials in URLs -> <redacted-secret>.
- `redact_pii`: emails, phone numbers, card numbers, SSN / Aadhaar numbers.
- `instruction_hits` / `instruction_lines`: lines that talk to the AI ("ignore your previous rules",
  "note for the AI", ...). They are only reported; the text stays, and understand reports it as a risk
  (ARCHITECTURE.md D3).
- `prepare_text`: the whole pipeline for one field, in the right order.
"""
import datetime
import html
import json
import re
import unicodedata
from urllib.parse import urlparse

REDACTED = "<redacted-secret>"
# UPDATED: size / depth limits so a huge or deeply nested ticket can't blow up cost or the recursion limit.
MAX_DEPTH = 30            # ADF nesting deeper than this is dropped (and counted as `truncated`)
MAX_CHARS = 60_000        # what the AI gets to see of one field
HARD_CAP = 400_000        # what we are willing to run regexes over

# UPDATED: extra node-kind sets so checklists, inline items and unknown containers are handled properly.
DROPPED = {"media", "mediaSingle", "mediaGroup", "mediaInline"}
LIST_KINDS = {"bulletList", "orderedList", "taskList", "decisionList"}
INLINE_KINDS = {"text", "hardBreak", "mention", "emoji", "status", "date", "inlineCard", "mediaInline",
                "inlineExtension", "placeholder"}
BLOCK_KINDS = {"paragraph", "heading", "bulletList", "orderedList", "taskList", "decisionList", "codeBlock",
               "blockquote", "table", "panel", "rule", "mediaSingle", "mediaGroup", "expand", "nestedExpand",
               "layoutSection", "bodiedExtension", "blockCard", "embedCard"}
# UPDATED: used to keep linked ticket keys (PROJ-123) from cards instead of a bare [link].
JIRA_KEY = re.compile(r"\b[A-Z][A-Z0-9]{1,9}-\d+\b")


# UPDATED: counts also track malformed nodes, truncation and hidden characters.
def _new_counts():
    return {"attachments": 0, "mentions": 0, "links": 0, "unknown": 0,
            "malformed": 0, "truncated": 0, "hidden_chars": 0}


# UPDATED: safe helpers - null content, non-dict nodes, bad attrs no longer crash (was AttributeError / TypeError).
def _s(value):
    return value if isinstance(value, str) else ("" if value is None else str(value))


def _kids(node):
    content = node.get("content") if isinstance(node, dict) else None
    return [k for k in content if isinstance(k, dict)] if isinstance(content, list) else []


def _attrs(node):
    attrs = node.get("attrs") if isinstance(node, dict) else None
    return attrs if isinstance(attrs, dict) else {}


def _int(value, default):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


# --- character hygiene ------------------------------------------------------------------------------

# UPDATED (new): character hygiene - zero-width / bidi / control chars, NBSP, CRLF, hidden Unicode-tag payloads.
_TAG_RUN = re.compile("[\U000e0020-\U000e007e]+")
_INVISIBLE = re.compile("[­​-\u200F\u202A-\u202E⁠-⁤\u2066-\u2069﻿"
                        "￹-￻\U000e0000-\U000e007f]")
_CONTROL = re.compile("[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]")
_ODD_SPACES = re.compile("[   -   　]")


def clean_text(text):
    """(text, hidden) - hidden = invisible / control characters removed. Hidden Unicode tag characters
    (an invisible way to smuggle in instructions) are decoded and shown as "[hidden text: ...]"."""
    text = _s(text)
    hidden = 0

    def tags(m):
        nonlocal hidden
        hidden += len(m.group(0))
        return " [hidden text: " + "".join(chr(ord(c) - 0xE0000) for c in m.group(0)) + "] "
    text = _TAG_RUN.sub(tags, text)
    text, n = _INVISIBLE.subn("", text)
    hidden += n
    text, n = _CONTROL.subn("", text)
    hidden += n
    text = text.replace(chr(13) + chr(10), chr(10)).replace(chr(13), chr(10))
    text = text.replace(chr(0x2028), chr(10)).replace(chr(0x2029), chr(10))
    text = _ODD_SPACES.sub(" ", text)
    text = re.sub(r"[ \t]+$", "", text, flags=re.M)
    return text, hidden


# UPDATED (new): output length cap, cut at a line boundary.
def _truncate(text, limit, counts):
    if limit is None or len(text) <= limit:
        return text
    cut = text.rfind("\n", 0, limit)
    counts["truncated"] += 1
    return text[:cut if cut > limit // 2 else limit].rstrip() + "\n[ticket text truncated]"


# --- rich text -> plain text ------------------------------------------------------------------------

# UPDATED: accepts str / JSON string / HTML / bytes / list (was: crashed on a plain-string description); caps length; cleans characters.
def adf_to_text(doc, max_chars=MAX_CHARS):
    """(text, counts) where counts = {attachments, mentions, links, unknown, malformed, truncated,
    hidden_chars}. Accepts an ADF dict / list of nodes, a JSON string of ADF, HTML or plain text."""
    counts = _new_counts()
    if isinstance(doc, (bytes, bytearray)):
        doc = bytes(doc).decode("utf-8", "replace")
    if isinstance(doc, str):
        stripped = doc.strip()
        if stripped[:1] in ("{", "["):
            try:
                doc = json.loads(stripped)
            except ValueError:
                pass
    if doc is None or doc == "" or doc == {} or doc == []:
        return "", counts
    if isinstance(doc, str):
        text = _html_to_text(doc) if re.search(r"<(?:p|div|br|ul|ol|li|h[1-6]|table)\b", doc, re.I) else doc
    else:
        if isinstance(doc, dict):
            nodes = _kids(doc) if doc.get("type") == "doc" else [doc]
        elif isinstance(doc, list):
            nodes = doc
        else:
            nodes = [{"type": "paragraph", "content": [{"type": "text", "text": str(doc)}]}]
        text = _join_blocks(nodes, counts)
    text, counts["hidden_chars"] = clean_text(text)
    text = text.strip()
    return _truncate(text, max_chars, counts), counts


# UPDATED (new): HTML bodies (renderedFields) -> text.
def _html_to_text(raw):
    raw = re.sub(r"(?is)<(script|style)\b.*?</\1>", "", raw)
    raw = re.sub(r"(?i)<br\s*/?>|</(?:p|div|h[1-6]|tr|table|ul|ol)>", "\n", raw)
    raw = re.sub(r"(?i)<li\b[^>]*>", "- ", raw)
    raw = re.sub(r"(?i)</t[dh]>", " | ", raw)
    raw = re.sub(r"<[^>]+>", "", raw)
    return re.sub(r"\n{3,}", "\n\n", html.unescape(raw))


# UPDATED: one malformed node is skipped and counted instead of failing the whole ticket.
def _join_blocks(nodes, counts, indent="", depth=0):
    parts = []
    for node in nodes:
        if not isinstance(node, dict):
            counts["malformed"] += 1
            continue
        part = _safe_block(node, counts, indent, depth)
        if part.strip():
            parts.append(part)
    return "\n\n".join(parts)


# UPDATED (new): per-node try/except.
def _safe_block(node, counts, indent, depth):
    try:
        return _block(node, counts, indent, depth)
    except Exception:           # includes RecursionError: one bad node must not lose the whole ticket
        counts["malformed"] += 1
        return ""


def _block(node, counts, indent="", depth=0):
    # UPDATED: depth guard.
    if depth > MAX_DEPTH:
        counts["truncated"] += 1
        return ""
    kind = node.get("type")
    content = _kids(node)
    attrs = _attrs(node)
    d = depth + 1
    if kind in DROPPED:
        return _media(node, counts, indent)
    # UPDATED: a bare text node used as a block is handled without counting it as 'unknown'.
    if kind == "text":
        return indent + _inline([node], counts, d)
    if kind == "paragraph":
        return indent + _inline(content, counts, d).strip("\n").replace("\n", "\n" + indent)
    if kind == "heading":
        # UPDATED: heading level clamped to 1-6, tolerant of bad values.
        level = min(max(_int(attrs.get("level"), 1), 1), 6)
        return indent + "#" * level + " " + _inline(content, counts, d).strip("\n").replace("\n", " ")
    if kind in ("bulletList", "orderedList"):
        # UPDATED: ordered-list start tolerates a string / missing value.
        start = _int(attrs.get("order"), 1) if kind == "orderedList" else None
        lines = []
        for i, item in enumerate(content):
            marker = f"{start + i}. " if start is not None else "- "
            lines.append(_list_item(item, counts, indent, marker, d))
        return "\n".join(lines)
    # UPDATED (new): checklists keep their state ([x] / [ ]); decisions are labelled.
    if kind in ("taskList", "decisionList"):
        return _task_list(node, counts, indent, d)
    if kind == "codeBlock":
        code = "".join(_s(t.get("text")) for t in content)
        longest = max((len(r) for r in re.findall(r"`+", code)), default=0)
        # UPDATED: dynamic fence (code containing ``` can't break out) + language kept; blank lines inside code are no longer collapsed.
        fence = "`" * max(3, longest + 1)
        lang = _s(attrs.get("language"))
        lang = lang if re.fullmatch(r"[\w+#.\-]{1,20}", lang) else ""
        return "\n".join(indent + line for line in [fence + lang, *code.split("\n"), fence])
    if kind == "blockquote":
        # UPDATED: blank quote lines keep their '>' prefix.
        inner = _join_blocks(content, counts, "", d)
        return "\n".join(indent + ("> " + line).rstrip() for line in inner.split("\n"))
    if kind == "rule":
        return indent + "---"
    if kind == "table":
        # UPDATED: tables get a header separator row and '|' inside cells is escaped.
        return _table(content, counts, indent, d)
    if kind in ("panel", "expand", "nestedExpand", "layoutSection", "layoutColumn", "bodiedExtension", "doc"):
        # UPDATED: warning / error / note panels keep their type; Jira macros become [macro: key] instead of vanishing.
        title = _s(attrs.get("title")).strip()
        if kind == "panel" and attrs.get("panelType") in ("warning", "error", "note"):
            title = title or f"[{attrs['panelType']}]"
        if kind == "bodiedExtension":
            counts["unknown"] += 1
            title = title or f"[macro: {_s(attrs.get('extensionKey'))}]"
        inner = _join_blocks(content, counts, indent, d)
        return (indent + title + "\n" + inner) if title else inner
    # UPDATED: embedCard handled; cards keep the Jira key / host (_link_label).
    if kind in ("blockCard", "embedCard"):
        counts["links"] += 1
        return indent + _link_label(attrs)
    if kind == "extension":
        counts["unknown"] += 1
        return indent + f"[macro: {_s(attrs.get('extensionKey')) or 'unknown'}]"
    # anything else: keep its text, never fail on an unknown element
    counts["unknown"] += 1
    if content:
        # UPDATED: unknown containers are rendered by what they contain (inline vs block), not a guess.
        if all(c.get("type") in INLINE_KINDS for c in content):
            return indent + _inline(content, counts, d)
        return _join_blocks(content, counts, indent, d)
    return indent + _s(node.get("text"))


# UPDATED: a list item that starts with a nested list keeps its marker; empty child blocks skipped.
def _list_item(item, counts, indent, marker, depth):
    pad = indent + " " * len(marker)
    lines, marked = [], False
    for child in _kids(item):
        if child.get("type") in LIST_KINDS:
            if not marked:
                lines.append(indent + marker.rstrip())
                marked = True
            lines.append(_safe_block(child, counts, indent + "  ", depth))
        else:
            text = _safe_block(child, counts, "", depth).strip("\n")
            if not text.strip():
                continue
            lines.append((pad if marked else indent + marker) + text.replace("\n", "\n" + pad))
            marked = True
    return "\n".join(l for l in lines if l.strip()) if lines else indent + marker.rstrip()


# UPDATED (new): taskItem / decisionItem rendering.
def _task_list(node, counts, indent, depth):
    lines = []
    for item in _kids(node):
        kind = item.get("type")
        if kind in LIST_KINDS:
            lines.append(_safe_block(item, counts, indent + "  ", depth))
            continue
        if kind == "decisionItem":
            marker = "- Decision: "
        else:
            marker = "- [x] " if _attrs(item).get("state") == "DONE" else "- [ ] "
        kids = _kids(item)
        if any(k.get("type") in BLOCK_KINDS for k in kids):
            body = _join_blocks(kids, counts, "", depth)
        else:
            body = _inline(kids, counts, depth)
        lines.append(indent + marker + body.strip("\n").replace("\n", "\n" + indent + " " * len(marker)))
    return "\n".join(lines)


# UPDATED (new): table renderer with header separator and escaping.
def _table(rows, counts, indent, depth):
    out = []
    for r, row in enumerate(rows):
        cells = _kids(row)
        texts = [_join_blocks(_kids(c), counts, "", depth).replace("\n", " ").replace("|", "\\|").strip()
                 for c in cells]
        out.append(indent + "| " + " | ".join(texts) + " |")
        if r == 0 and cells and all(c.get("type") == "tableHeader" for c in cells):
            out.append(indent + "| " + " | ".join("---" for _ in cells) + " |")
    return "\n".join(out)


# UPDATED (new): images keep alt text / caption as [image: ...]; media group counted per file.
def _media(node, counts, indent):
    own = node.get("type") in ("media", "mediaInline")
    items = [node] if own else [k for k in _kids(node) if k.get("type") in DROPPED]
    counts["attachments"] += max(1, len(items))
    labels = []
    for m in items:
        alt = " ".join(_s(_attrs(m).get("alt")).split())[:200]
        if alt:
            labels.append(alt)
    for caption in (k for k in _kids(node) if k.get("type") == "caption"):
        text = " ".join(_inline(_kids(caption), counts, 1).split())[:200]
        if text:
            labels.append(text)
    return indent + f"[image: {'; '.join(labels)}]" if labels else ""


# UPDATED (new): keeps the Jira key (or host) of a card link, drops the full URL.
def _link_label(attrs):
    """'[link: PROJ-123]' or '[link: host]' - the target is dropped but the Jira key / host is kept."""
    url = _s(attrs.get("url"))
    data = attrs.get("data")
    if not url and isinstance(data, dict):
        url = _s(data.get("url"))
    match = JIRA_KEY.search(url)
    if match:
        return f"[link: {match.group(0)}]"
    try:
        host = urlparse(url).hostname
    except ValueError:
        host = None
    return f"[link: {host}]" if host else "[link]"


# UPDATED: date nodes print YYYY-MM-DD instead of a raw epoch-millisecond number.
def _fmt_date(attrs):
    stamp = attrs.get("timestamp")
    try:
        return datetime.datetime.fromtimestamp(int(stamp) / 1000, datetime.timezone.utc).strftime("%Y-%m-%d")
    except (TypeError, ValueError, OverflowError, OSError):
        return _s(attrs.get("text")) or _s(stamp)


# UPDATED: tolerates bad nodes; struck-out text is shown as ~~removed~~ (it is a deleted requirement); backticks inside inline code are escaped; links counted once per link.
def _inline(nodes, counts, depth=0):
    if depth > MAX_DEPTH:
        counts["truncated"] += 1
        return ""
    out, last_href = [], None
    for n in nodes:
        if not isinstance(n, dict):
            counts["malformed"] += 1
            continue
        try:
            kind = n.get("type")
            attrs = _attrs(n)
            if kind == "text":
                text = _s(n.get("text"))
                marks = [m for m in (n.get("marks") or []) if isinstance(m, dict)]
                types = {m.get("type") for m in marks}
                href = next((_s(_attrs(m).get("href")) for m in marks if m.get("type") == "link"), None)
                if "link" in types and href != last_href:
                    counts["links"] += 1
                last_href = href if "link" in types else None
                if "code" in types and text:
                    tick = "``" if "`" in text else "`"
                    text = f"{tick}{text}{tick}"
                if "strike" in types and text.strip():
                    text = f"~~{text}~~"
                out.append(text)
                continue
            last_href = None
            if kind == "hardBreak":
                out.append("\n")
            elif kind == "mention":
                counts["mentions"] += 1
                out.append("(someone)")
            elif kind == "inlineCard":
                counts["links"] += 1
                out.append(_link_label(attrs))
            elif kind == "emoji":
                out.append(_s(attrs.get("text")) or _s(attrs.get("shortName")))
            elif kind == "status":
                out.append(_s(attrs.get("text")))
            elif kind == "date":
                out.append(_fmt_date(attrs))
            elif kind == "placeholder":
                out.append(_s(attrs.get("text")))
            elif kind in DROPPED:
                counts["attachments"] += 1
            elif kind == "inlineExtension":
                counts["unknown"] += 1
                out.append(f"[macro: {_s(attrs.get('extensionKey')) or 'unknown'}]")
            else:
                counts["unknown"] += 1
                kids = _kids(n)
                out.append(_inline(kids, counts, depth + 1) if kids else _s(n.get("text")))
        except Exception:
            counts["malformed"] += 1
    return "".join(out)


# --- secrets ----------------------------------------------------------------------------------------
# Patterns with a group named `s` redact only that group; the others are replaced whole.

# UPDATED: added Stripe (sk_live_), GitLab, npm, case-insensitive Bearer / Authorization headers, credentials inside URLs, truncated private keys, long base64-ish tokens.
DIRECT_PATTERNS = [
    # a private key, including one that was cut off before its END line
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?(?:-----END [A-Z ]*PRIVATE KEY-----|\Z)"),
    re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}"),              # JWT
    re.compile(r"\bsk-(?:[a-z]+-){0,3}[A-Za-z0-9_-]{16,}"),                                    # OpenAI / OpenRouter / Anthropic
    re.compile(r"\b[spr]k_(?:live|test)_[A-Za-z0-9]{10,}"),                                    # Stripe
    re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|glpat-[A-Za-z0-9_-]{20,})"),
    re.compile(r"\bnpm_[A-Za-z0-9]{30,}"),
    re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b"),                                              # AWS access key id
    re.compile(r"\bATATT[A-Za-z0-9_\-=]{20,}"),                                                # Atlassian API token
    re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b"),                                                  # Google API key
    re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}"),                                             # Slack
    re.compile(r"\bauthorization[\"']?\s*[:=]\s*[\"']?(?:basic|bearer|token|digest)[ \t]+(?P<s>[^\s\"']{8,})", re.I),
    re.compile(r"\bbearer[ \t]+(?P<s>(?=[A-Za-z0-9._~+/=-]*\d)[A-Za-z0-9._~+/=-]{16,})", re.I),
    # user:password@host inside any URL (postgres://, https://, ...)
    re.compile(r"\b[a-z][a-z0-9+.\-]{0,19}://[^\s/:@]{1,100}:(?P<s>[^\s/@]{1,200})(?=@)", re.I),  # UPDATED: bounded (was quadratic on long input)
    # long mixed-case token with digits (base64-ish); skips paths and kebab-case slugs
    re.compile(r"\b(?=[A-Za-z0-9_+-]{0,200}[A-Z])(?=[A-Za-z0-9_+-]{0,200}[a-z])(?=[A-Za-z0-9_+-]{0,200}\d)[A-Za-z0-9_+-]{40,}={0,2}"),
]

# UPDATED (new): NAME=value / JSON / env-style names (DB_PASSWORD=, API_KEY=, "password": "x") - were missed by the old regex.
_NAME_WORDS = (r"(?:pass(?:word|wd|code|phrase)s?|pwd|secret|token|api[_\-]?key|apikey|access[_\-]?key"
               r"|private[_\-]?key|auth[_\-]?key|signing[_\-]?key)")
_VALUE = r"(?P<val>\"[^\"\n]*\"|'[^'\n]*'|`[^`\n]*`|[^\s,;]+)"
# NAME = value, NAME: value, "name": "value" - including DB_PASSWORD=..., API_KEY=...
# UPDATED: bounded prefix (no catastrophic backtracking); handles quotes between name and ':'.
ASSIGNMENT = re.compile(r"(?P<name>\b[\w.\-]{0,40}?" + _NAME_WORDS + r"[\w.\-]{0,20})"
                        r"(?P<mid>[\"'`]?[ \t]*[:=][ \t]*)" + _VALUE, re.I)
# "password Rooks@Secret2026!", "my password is: abc123", "api key abc123..."
# UPDATED: separator is [ 	] only (was \s, which crossed lines); bare 'pass' removed (it redacted 'pass e2e-tests'); plurals handled.
PROSE = re.compile(r"\b(?P<name>pass(?:word|wd|code|phrase)s?|pwd|secret|token|api[ _\-]?key|access[ _\-]?key"
                   r"|client[ _\-]?secret|private[ _\-]?key)\b"
                   r"(?P<mid>[ \t]*[:=][ \t]*|[ \t]+(?:is|are|was)[ \t]*:?[ \t]*|[ \t]+)" + _VALUE, re.I)
# "creds: admin / Admin@123"
# UPDATED (new): 'creds: admin / Admin@123' pairs.
CREDENTIAL_PAIR = re.compile(r"\b(?:creds?|credentials?|logins?)\b[ \t]*(?:[:=\-]|is|are)[ \t]*"
                             r"(?P<user>[^\s/]+)[ \t]*/[ \t]*(?P<val>[^\s,;]+)", re.I)

# UPDATED (new): placeholders / stop-words so '<password>', '${PASSWORD}', 'password: required' are not redacted.
PLACEHOLDER = re.compile(r"<[^>]*>|\$\{?\w+\}?|\{\{.*\}\}|%\w+%|[*•xX#._\-]{3,}|https?://\S*", re.I)
PLACEHOLDER_WORDS = {"null", "none", "nil", "true", "false", "undefined", "empty", "blank", "password",
                     "secret", "token", "string", "value", "example", "changeme", "yourpassword", "na", "n/a"}
STOP_WORDS = {"required", "optional", "invalid", "incorrect", "missing", "wrong", "valid", "correct", "expired",
              "hidden", "masked", "visible", "mandatory", "encrypted", "changed", "updated", "cleared",
              "disabled", "enabled", "unchanged", "provided", "entered", "stored", "confirmed", "reset",
              "verification", "authentication", "authorization", "protected", "complexity", "validation",
              "recovery", "expiry", "policy", "strength", "length", "should", "cannot", "forgotten"}


# UPDATED: symbol must be a real special char (not '-' or '_'), kebab-case words and versions are not secrets ('token (JWT)', 'password re-entry' no longer redacted).
def _looks_secret(value):
    """True for values with a letter AND (a digit or a symbol); plain words / kebab-case words are not."""
    v = value.strip("()[]{}<>\"'`").rstrip(".,;:")
    if len(v) < 6 or REDACTED in v or not re.search(r"[A-Za-z]", v):
        return False
    if re.fullmatch(r"v?\d+(?:\.\d+)+", v) or re.fullmatch(r"[a-z0-9]+(?:[-_.][a-z0-9]+)+", v):
        return False
    return bool(re.search(r"\d", v) or re.search(r"[@#$%^&*!?+=~]", v.rstrip("!?")))


# UPDATED (new): context-aware decision - explicit 'password: 123456' / 'password: letmein' are now caught.
def _should_redact(val, name, explicit):
    quoted = len(val) >= 2 and val[0] in "\"'`" and val[-1] == val[0]
    v = val[1:-1] if quoted else val.strip("([{\"'`").rstrip(".,;)]}'\"`")
    if len(v) < 3 or REDACTED in v or PLACEHOLDER.fullmatch(v) or v.lower() in PLACEHOLDER_WORDS:
        return False
    if _looks_secret(v):
        return True
    if not explicit:
        return False
    if quoted:
        return True
    if re.fullmatch(r"\d{6,}", v):
        return True
    if len(v) >= 4 and re.search(r"[_.\-]", name) and v.lower() not in STOP_WORDS:   # DB_PASSWORD=abcd
        return True
    return bool(re.match(r"pass|pwd", name, re.I) and v.isalpha() and v.islower()      # password: letmein
                and len(v) >= 6 and v not in STOP_WORDS)


def _redact_direct(pattern, text):
    count = 0

    def repl(m):
        nonlocal count
        if "s" in pattern.groupindex:
            secret = m.group("s")
            if secret is None or REDACTED in secret:
                return m.group(0)
            count += 1
            a, b = m.span("s")
            whole, o = m.group(0), m.start()
            return whole[:a - o] + REDACTED + whole[b - o:]
        count += 1
        return REDACTED
    return pattern.sub(repl, text), count


def _redact_val(pattern, text, explicit_if):
    count = 0

    def repl(m):
        nonlocal count
        explicit = explicit_if(m)
        if not _should_redact(m.group("val"), m.groupdict().get("name") or "credential", explicit):
            return m.group(0)
        count += 1
        a, b = m.span("val")
        whole, o = m.group(0), m.start()
        val = m.group("val")
        tail = val[len(val.rstrip(".,;)]}")):] if not val[:1] in "\"'`" else ""
        return whole[:a - o] + REDACTED + tail
    return pattern.sub(repl, text), count


# UPDATED: runs direct patterns, then assignment / prose / credential-pair rules.
def redact_secrets(text):
    """(text, how many secrets were replaced)."""
    text, count = _s(text), 0
    for pattern in DIRECT_PATTERNS:
        text, n = _redact_direct(pattern, text)
        count += n
    for pattern, explicit_if in ((ASSIGNMENT, lambda m: True),
                                 (PROSE, lambda m: bool(re.search(r"[:=]|\b(?:is|are|was)\b", m.group("mid")))),
                                 (CREDENTIAL_PAIR, lambda m: True)):
        text, n = _redact_val(pattern, text, explicit_if)
        count += n
    return text, count


# --- personal data ----------------------------------------------------------------------------------

# UPDATED (new): personal data redaction (emails, Luhn-checked cards, SSN / Aadhaar, phones).
EMAIL = re.compile(r"(?<![\w.+-])[\w.+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+")
PHONE = re.compile(r"(?<![\w.])(?:\+\d|\(?\d)[\d ().\-]{7,17}\d(?![\w-])")
CARD = re.compile(r"(?<![\w.-])\d(?:[ -]?\d){12,18}(?![\w.-])")
SSN = re.compile(r"(?<![\w-])\d{3}-\d{2}-\d{4}(?![\w-])")
AADHAAR = re.compile(r"(?<![\w-])\d{4} \d{4} \d{4}(?![\w-])")


def _luhn(digits):
    total = 0
    for i, ch in enumerate(reversed(digits)):
        n = int(ch)
        if i % 2:
            n = n * 2 - 9 if n > 4 else n * 2
        total += n
    return total % 10 == 0


def redact_pii(text):
    """(text, how many items were replaced): emails, card numbers (Luhn-checked), SSN / Aadhaar, phones."""
    text, count = _s(text), 0

    def sub(pattern, label, check=None):
        nonlocal text, count

        def repl(m):
            nonlocal count
            if check and not check(m.group(0)):
                return m.group(0)
            count += 1
            return f"<redacted-{label}>"
        text = pattern.sub(repl, text)

    def digits(s):
        return re.sub(r"\D", "", s)
    sub(EMAIL, "email")
    sub(CARD, "card", lambda s: 13 <= len(digits(s)) <= 19 and _luhn(digits(s)))
    sub(SSN, "id")
    sub(AADHAAR, "id")
    sub(PHONE, "phone", lambda s: 10 <= len(digits(s)) <= 15 and bool(re.search(r"[+ ().\-]", s))
        and not re.fullmatch(r"\d{4}-\d{2}-\d{2}.*", s))
    return text, count


# --- text aimed at the AI ---------------------------------------------------------------------------

# UPDATED: AI-word list narrowed ('model', 'agent', 'tool' alone caused false positives).
AI = (r"(?:ai|a\.i\.|assistant|bot|llm|chatgpt|gpt|claude|gemini|copilot|language model|ai model|ai agent"
      r"|automated (?:agent|reviewer|tool))")
NOUN = r"(?:rules|instructions|prompts?|guidelines|directions|guardrails|policies|context|messages|programming)"
# UPDATED: patterns rewritten - 'ignore the above' / 'new instructions:' / chat-template tokens added; false positives removed ('override pricing rules', 'show the password', 'mark the todo as done', 'QA sign-off required').
INSTRUCTION_PATTERNS = [
    re.compile(rf"\b(?:ignore|disregard|forget|override|bypass)\s+(?:(?:all|any|the|your|my|these|those|every|of)\s+)*"
               rf"(?:previous|prior|above|earlier|preceding|original|system|safety)\b[^.\n]{{0,40}}\b{NOUN}\b"),
    re.compile(r"\b(?:ignore|disregard|forget)\s+(?:all\s+)?(?:of\s+)?(?:the\s+)?above\b"),
    re.compile(r"\b(?:ignore|disregard|forget)\s+(?:everything|anything)\s+(?:above|before|else|previously)\b"),
    re.compile(rf"\b(?:ignore|disregard|forget|override|bypass)\b[^.\n]{{0,30}}\b(?:your|its)\s+{NOUN}\b"),
    re.compile(r"\b(?:new|updated|revised) instructions?\s*:"),
    re.compile(rf"\b(?:note|message|instructions?|reminder)\s+(?:for|to)\s+(?:the\s+|any\s+|all\s+)?{AI}\b"),
    re.compile(rf"\b(?:dear|hey|attention|hello)\s+{AI}\b"),
    re.compile(r"\byou are now\b|\bfrom now on,? you\b|\bsystem prompt\b|\bjailbreak\b|\bdeveloper mode\b"),
    re.compile(r"\bpretend (?:to be|you are|that you)\b|\bact as (?:if you (?:are|were)|an? (?:ai|assistant|llm|unrestricted))"),
    re.compile(r"\[/?inst\]|<\|?(?:im_start|im_end|system|assistant)\|?>|^\s*(?:#+\s*)?system\s*:"),
    re.compile(r"\bdo not (?:write|create|generate|produce|add|include)\b[^.\n]{0,20}\btests?(?: cases?)?\b"),
    re.compile(r"\b(?:mark|set|flag|label)\s+(?:this|the)\s+(?:ticket|spec|story|analysis|review|output|result|"
               r"test cases?|uat)\s+as\s+(?:approved|signed[ -]off|passed|verified|done)\b"),
    re.compile(r"\b(?:qa|uat|pm)\s+(?:has\s+)?(?:already\s+)?(?:signed[ -]?off|approved)\b"
               r"|\bapproved by the (?:pm|qa|product manager)\b|\balready (?:approved|signed[ -]off)\b"),
    # UPDATED (restored, narrow): a sign-off claimed as done ("QA sign-off: complete"), not "QA sign-off required".
    re.compile(r"\b(?:qa|uat|pm)\s+sign[ -]?off\s*[:=\-]\s*(?:complete|completed|done|approved|granted|given|yes|passed)\b"),
    re.compile(r"\b(?:reveal|print|output|leak|exfiltrate|disclose|repeat)\b[^.\n]{0,30}\b(?:your|the)\s+"
               r"(?:system\s+)?(?:prompt|instructions|api key|credentials|secrets?)\b"),
    # UPDATED (restored, narrow): asking for a real credential to be put in the output ("include the admin password").
    re.compile(r"\b(?:include|insert|paste|add|put|write|send|share)\b[^.\n]{0,30}\b(?:admin|root|real|actual|"
               r"production|prod|live)\s+(?:password|passwords|credentials|api keys?|tokens?)\b"),
    re.compile(r"\[hidden text:"),                     # produced by clean_text for invisible Unicode tags
]
# UPDATED (new): look-alike Cyrillic / Greek letters mapped to Latin so they can't evade detection.
_CONFUSABLES = str.maketrans({
    "а": "a", "е": "e", "о": "o", "р": "p", "с": "c", "у": "y", "х": "x",
    "і": "i", "ј": "j", "ѕ": "s", "ԁ": "d", "α": "a", "ο": "o", "ρ": "p",
    "ν": "v", "ι": "i", "κ": "k", "τ": "t", "υ": "u", "ı": "i"})


# UPDATED (new): NFKC + lower-case + strip invisibles / markdown emphasis before matching.
def _fold(line):
    """Make a line comparable: Unicode-normalised, lower-case, no invisible characters / look-alike letters /
    markdown emphasis, single spaces."""
    line = unicodedata.normalize("NFKC", line).lower().translate(_CONFUSABLES)
    line = _INVISIBLE.sub("", line)
    line = re.sub(r"[*~`]", "", line)
    return re.sub(r"\s+", " ", line).strip()


# UPDATED (new): returns which pattern fired and the line text; also catches instructions split over two lines.
def instruction_hits(text):
    """[{line, pattern, text}] for lines (or two consecutive lines) that look like instructions to the AI."""
    lines = _s(text).split("\n")
    folded = [_fold(l) for l in lines]
    hits, seen = [], set()

    def first_match(s):
        return next((i for i, p in enumerate(INSTRUCTION_PATTERNS) if p.search(s)), None)

    for i, f in enumerate(folded):
        idx = first_match(f)
        if idx is not None:
            hits.append({"line": i + 1, "pattern": idx, "text": lines[i].strip()[:200]})
            seen.add(i)
    for i in range(len(folded) - 1):            # an instruction split over two lines
        if i in seen or i + 1 in seen or not folded[i] or not folded[i + 1]:
            continue
        idx = first_match(folded[i] + " " + folded[i + 1])
        if idx is not None:
            hits.append({"line": i + 1, "pattern": idx, "text": lines[i].strip()[:200]})
            hits.append({"line": i + 2, "pattern": idx, "text": lines[i + 1].strip()[:200]})
    return sorted(hits, key=lambda h: h["line"])


# UPDATED: now built on instruction_hits (same return type as before).
def instruction_lines(text):
    """Line numbers (1-based) of lines that look like instructions to the AI."""
    return sorted({h["line"] for h in instruction_hits(text)})


# --- file names -------------------------------------------------------------------------------------

# UPDATED: many more extensions; paths keep dots and [brackets]; 'Node.js'-style names and URLs are ignored; Windows paths handled.
_EXT = (r"tsx|ts|jsx|js|mjs|cjs|css|scss|sass|less|html|htm|vue|svelte|json|ya?ml|mdx|md|py|java|kt|go|rs|rb"
        r"|php|sql|xml|properties|gradle|sh")
FILE_NAME = re.compile(r"(?<![\w@.\-/])(?:\.{0,2}/)?(?:[\w@.\-\[\]$+~]+/)*[\w@.\-\[\]$+~]*\.(?:" + _EXT + r")(?![\w])",
                       re.I)
FRAMEWORKS = {"node.js", "next.js", "vue.js", "react.js", "nuxt.js", "express.js", "chart.js", "d3.js",
              "three.js", "angular.js", "backbone.js", "ember.js", "nest.js", "deno.js", "nx.js", "p5.js"}


# UPDATED: see FILE_NAME note above.
def file_names(text):
    """Source / config file names mentioned in the text (paths with dots and [brackets] kept; "Node.js",
    URLs and Windows separators handled)."""
    text = re.sub(r"https?://\S+", " ", _s(text)).replace("\\", "/")
    found = set()
    for name in FILE_NAME.findall(text):
        name = re.sub(r"^(?:\./|/)+", "", name)
        if name and name.lower() not in FRAMEWORKS:
            found.add(name)
    return sorted(found)


# --- the whole pipeline -----------------------------------------------------------------------------

# UPDATED (new): the whole pipeline in the right order (convert -> clean -> redact -> truncate -> detect).
def prepare_text(doc, pii=True, max_chars=MAX_CHARS):
    """One ticket field -> {text, counts, secrets_redacted, pii_redacted, instruction_lines,
    instruction_hits, files}. Order matters: convert, clean, redact, THEN detect and truncate."""
    text, counts = adf_to_text(doc, max_chars=HARD_CAP)
    text, secrets = redact_secrets(text)
    found_pii = 0
    if pii:
        text, found_pii = redact_pii(text)
    text = _truncate(text, max_chars, counts)
    hits = instruction_hits(text)
    return {"text": text, "counts": counts, "secrets_redacted": secrets, "pii_redacted": found_pii,
            "instruction_lines": sorted({h["line"] for h in hits}), "instruction_hits": hits,
            "files": file_names(text)}
