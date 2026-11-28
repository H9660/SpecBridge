"""Terminal look of a run: the SpecBridge banner and coloured progress lines (stdlib only, ANSI colours).

The graph logs plain lines to the "specbridge.progress" logger (graph.py, criterion_worker.py). `ProgressFormatter`
reads those lines and prints them with one colour per node and per worker. Colours are off when the stream is not
a terminal or NO_COLOR is set; FORCE_COLOR turns them on. Without colours the lines read as they always did.
"""
import logging
import os
import re
import sys

RESET, BOLD, DIM = "\033[0m", "\033[1m", "\033[2m"


def _fg(n):
    return f"\033[38;5;{n}m"


NODE_COLORS = {"intake": 45, "understand": 75, "clarify": 220, "orchestrator": 177, "merge": 114,
               "reviewer": 209, "render": 80, "save_local": 120, "publish": 120}
WORKER_COLORS = [81, 213, 156, 215, 147, 123, 186, 183]   # W1, W2, ... cycle through these
E2E_COLOR = 205
STATUS_COLORS = {"complete": 82, "error": 196}            # anything else (needs_more, budget_hit, ...) is amber
AMBER = 214
TOOL_COLOR = 250

LETTERS = {
    "S": ["███████╗", "██╔════╝", "███████╗", "╚════██║", "███████║", "╚══════╝"],
    "P": ["██████╗ ", "██╔══██╗", "██████╔╝", "██╔═══╝ ", "██║     ", "╚═╝     "],
    "E": ["███████╗", "██╔════╝", "█████╗  ", "██╔══╝  ", "███████╗", "╚══════╝"],
    "C": [" ██████╗", "██╔════╝", "██║     ", "██║     ", "╚██████╗", " ╚═════╝"],
    "B": ["██████╗ ", "██╔══██╗", "██████╔╝", "██╔══██╗", "██████╔╝", "╚═════╝ "],
    "R": ["██████╗ ", "██╔══██╗", "██████╔╝", "██╔══██╗", "██║  ██║", "╚═╝  ╚═╝"],
    "I": ["██╗", "██║", "██║", "██║", "██║", "╚═╝"],
    "D": ["██████╗ ", "██╔══██╗", "██║  ██║", "██║  ██║", "██████╔╝", "╚═════╝ "],
    "G": [" ██████╗ ", "██╔════╝ ", "██║  ███╗", "██║   ██║", "╚██████╔╝", " ╚═════╝ "],
}
TAGLINE = "Jira ticket in. Real-code UAT test cases out."


def color_enabled(stream):
    """Colours only on a terminal (or when FORCE_COLOR is set), never when NO_COLOR is set."""
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("FORCE_COLOR"):
        return True
    return bool(getattr(stream, "isatty", lambda: False)())


def enable_windows_ansi():
    """Windows consoles need this once before they show ANSI colours (a no-op elsewhere)."""
    if os.name == "nt":
        os.system("")


def banner(use_color=True):
    """The SpecBridge logo: SPEC in cyan, BRIDGE in violet, with a shadow line under each."""
    rows = []
    for r in range(6):
        spec = "".join(LETTERS[ch][r] for ch in "SPEC")
        bridge = "".join(LETTERS[ch][r] for ch in "BRIDGE")
        rows.append((spec, bridge))
    out = [""]
    for spec, bridge in rows:
        out.append("  " + (f"{_fg(45)}{spec}{_fg(141)}{bridge}{RESET}" if use_color else spec + bridge))
    tag = "  " + TAGLINE
    out += ["", f"{DIM}{tag}{RESET}" if use_color else tag, ""]
    return "\n".join(out)


def _paint(text, color, *styles):
    return f"{''.join(styles)}{_fg(color)}{text}{RESET}"


def worker_color(worker_id):
    """A steady colour per worker: W1, W2, ... cycle; the end-to-end worker has its own."""
    if worker_id.upper().startswith("E2E"):
        return E2E_COLOR
    m = re.search(r"\d+", worker_id)
    return WORKER_COLORS[(int(m.group()) - 1) % len(WORKER_COLORS)] if m else WORKER_COLORS[0]


# the progress lines graph.py and criterion_worker.py write
WORKER_START = re.compile(r"^-> worker (\S+) started \((.*)\)$")
WORKER_TOOL = re.compile(r"^\s+worker (\S+) tool (\d+)/(\d+): (\w+)\((.*)\)$")
WORKER_WRITE = re.compile(r"^\s+worker (\S+) writing test cases (.*)$")
WORKER_DONE = re.compile(r"^\s+worker (\S+) (\w+) in ([\d.]+)s - (.*)$")
SLM_EVENT = re.compile(r"^\s+SLM host (\S+) (\w+)(?:: (.*))?$")      # slm_pool.py (ADR D31)
SLM_EVENT_COLORS = {"down": 196, "misconfigured": 196, "back": 82, "moved": 214}
NODE_START = re.compile(r"^-> (\w+)$")
NODE_DONE = re.compile(r"^\s+(\w+) done in ([\d.]+)s(?: - (.*))?$")


class ProgressFormatter(logging.Formatter):
    """Time stamp, then a coloured line per node or worker. Unknown lines are shown dim."""

    def __init__(self, use_color=True):
        super().__init__(datefmt="%H:%M:%S")
        self.use_color = use_color

    def format(self, record):
        msg = record.getMessage()
        stamp = self.formatTime(record, self.datefmt)
        if not self.use_color:
            return f"{stamp} {msg}"
        return f"{DIM}{stamp}{RESET} {self._colour(msg)}"

    def _colour(self, msg):
        if m := WORKER_START.match(msg):
            wid, criteria = m.groups()
            c = worker_color(wid)
            return f"  {_paint('▶ ' + wid, c, BOLD)} {_paint('started', c)} {DIM}{criteria}{RESET}"
        if m := WORKER_TOOL.match(msg):
            wid, i, n, tool, args = m.groups()
            c = worker_color(wid)
            return (f"  {_paint('│ ' + wid, c)} {DIM}{i}/{n}{RESET} {_paint(tool, TOOL_COLOR, BOLD)}"
                    f"{DIM}({args}){RESET}")
        if m := WORKER_WRITE.match(msg):
            wid, rest = m.groups()
            c = worker_color(wid)
            return f"  {_paint('│ ' + wid, c)} {_paint('writing test cases', c)} {DIM}{rest}{RESET}"
        if m := WORKER_DONE.match(msg):
            wid, status, secs, rest = m.groups()
            c = worker_color(wid)
            sc = STATUS_COLORS.get(status, AMBER)
            mark = "✔" if status == "complete" else "✖" if status == "error" else "!"
            return (f"  {_paint(mark + ' ' + wid, c, BOLD)} {_paint(status, sc, BOLD)} "
                    f"{DIM}in {secs}s - {RESET}{rest}")
        if m := SLM_EVENT.match(msg):
            host, kind, detail = m.groups()
            c = SLM_EVENT_COLORS.get(kind, AMBER)
            return (f"  {_paint('◆ SLM ' + host, c, BOLD)} {_paint(kind, c)}"
                    + (f" {DIM}{detail}{RESET}" if detail else ""))
        if m := NODE_START.match(msg):
            name = m.group(1)
            return _paint(f"▶ {name}", NODE_COLORS.get(name, 250), BOLD)
        if m := NODE_DONE.match(msg):
            name, secs, detail = m.groups()
            c = NODE_COLORS.get(name, 250)
            return (f"{_paint('✔ ' + name, c, BOLD)} {DIM}{secs}s{RESET}"
                    + (f"  {_paint(detail, c)}" if detail else ""))
        return f"{DIM}{msg}{RESET}"


def install_progress_log(stream=None):
    """Attach the coloured progress printer to the progress logger (what run_ticket.py does unless --quiet)."""
    stream = stream or sys.stderr
    use_color = color_enabled(stream)
    if use_color:
        enable_windows_ansi()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(ProgressFormatter(use_color))
    log = logging.getLogger("specbridge.progress")
    log.addHandler(handler)
    log.setLevel(logging.INFO)
    log.propagate = False
    return use_color
