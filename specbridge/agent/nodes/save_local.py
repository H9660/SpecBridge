"""save_local (node 10, code only: no AI, no network): in dry-run and eval mode, write the page render made to files.

One folder per run, next to its run record:
  data/runs/<ticket>/<run_id>/page.html          open in a browser
                              page.md            the Markdown copy
                              page.storage.xml   exactly what publish would send to Confluence
                              comment.txt        exactly what publish would post on the ticket ({page_url} kept)
The run record itself is still written by run_ticket at the very end (only it knows the final status).
Folder names come only from the checked ticket key and run id, never from ticket or AI text, and must stay inside
data/runs/. Each file is written to a temporary name and renamed, so a crash never leaves half a page. A last scan
redacts any secret-like text (render already did; a hit is a warning) and checks that the storage copy is
well-formed XML (a warning, so publish knows to refuse it). A write error never crashes the run: the page stays in
the state and the record, and the error is reported.
Out: state["saved"] = {folder, files, bytes, warnings, error}.
"""
import os
import re
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

from specbridge import ticket_text
from specbridge.agent import run_record

FILES = {"html": "page.html", "markdown": "page.md", "storage": "page.storage.xml", "comment": "comment.txt"}
RUN_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}")      # the same rule as START
KEY = re.compile(r"[A-Z][A-Z0-9]+-\d+|unknown")


class SaveError(Exception):
    pass


def folder_for(state, records_dir):
    """data/runs/<ticket>/<run_id>/, checked again: a safe key and run id, and inside records_dir."""
    run_id = str(state.get("run_id") or "")
    if not RUN_ID.fullmatch(run_id) or set(run_id) == {"."}:
        raise SaveError(f"unsafe run id {run_id[:80]!r}")
    record = run_record.path_for(state, records_dir)
    key = record.parent.name
    if not KEY.fullmatch(key):
        raise SaveError(f"unsafe ticket key {key[:80]!r}")
    root = Path(records_dir).resolve()
    folder = (root / key / run_id).resolve()
    if root not in folder.parents:
        raise SaveError("the folder would be outside the runs folder")
    return folder


def well_formed(storage):
    try:
        ET.fromstring(f'<root xmlns:ac="urn:ac" xmlns:ri="urn:ri">{storage}</root>')
        return True
    except ET.ParseError:
        return False


def _file_mode():
    """The mode a normal new file gets here (0o666 minus the umask); mkstemp would leave it private (0o600)."""
    mask = os.umask(0)
    os.umask(mask)
    return 0o666 & ~mask


FILE_MODE = _file_mode()


def write_atomic(path, text):
    """Write to a temporary file in the same folder, then rename over the target."""
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        os.chmod(tmp, FILE_MODE)
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def save(state, records_dir):
    page = state.get("page")
    empty = {"folder": None, "files": {}, "bytes": 0, "warnings": []}
    if not page:
        return {**empty, "error": "no page to save"}
    try:
        folder = folder_for(state, records_dir)
    except SaveError as err:
        return {**empty, "error": f"not saved: {err}"}
    warnings, texts = [], {}
    for kind, name in FILES.items():
        text, found = ticket_text.redact_secrets(str(page.get(kind) or ""))
        if found:
            warnings.append(f"{name}: {found} secret-like text(s) redacted before saving")
        texts[kind] = text
    if not well_formed(texts["storage"]):
        warnings.append("page.storage.xml is not well-formed XML, so publish must refuse it")
    try:
        folder.mkdir(parents=True, exist_ok=True)
        for kind, name in FILES.items():
            write_atomic(folder / name, texts[kind])
    except OSError as err:
        return {**empty, "folder": str(folder), "warnings": warnings,
                "error": f"files could not be saved: {type(err).__name__}: {err}"}
    return {"folder": str(folder), "files": {kind: str(folder / name) for kind, name in FILES.items()},
            "bytes": sum(len(t.encode("utf-8")) for t in texts.values()), "warnings": warnings, "error": ""}


def make_node(records_dir=None):
    """records_dir: where the run records go (run_ticket passes its own; tests pass a temporary folder)."""
    def node(state, settings):
        return {"saved": save(state, Path(records_dir or run_record.RUNS))}
    return node


node = make_node()
