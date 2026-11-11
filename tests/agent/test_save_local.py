"""Node 10 - save_local: in dry-run and eval mode, the page render made is written to data/runs/<ticket>/<run_id>/
(page.html, page.md, page.storage.xml, comment.txt) - safely, atomically, never outside the runs folder."""
import json
import os

import pytest

from specbridge.agent.limits import Settings
from specbridge.agent.nodes import save_local
from specbridge.agent.nodes.save_local import FILES, make_node

PAGE = {"title": "UAT SPEC-12: Keyboard", "labels": ["spec-12"], "storage": "<h2>1. Summary</h2><p>ok &amp; fine</p>",
        "html": "<!doctype html>\n<html><body><p>ü – page</p></body></html>\n", "markdown": "# UAT SPEC-12\n\nü\n",
        "comment": "[SpecBridge] SPEC-12: ready\nPage: {page_url}", "summary": {"kind": "test-plan"}}


def state(**extra):
    return {"run_id": "20261111-120000-abc123", "mode": "dry-run", "ticket": {"key": "SPEC-12"}, "page": dict(PAGE),
            **extra}


def save(st, records):
    return make_node(records)(st, Settings())["saved"]


def test_writes_the_four_files_with_exactly_the_pages_texts(records):
    saved = save(state(), records)
    folder = records / "SPEC-12" / "20261111-120000-abc123"
    assert saved["error"] == "" and saved["warnings"] == [] and saved["folder"] == str(folder.resolve())
    assert sorted(p.name for p in folder.iterdir()) == ["comment.txt", "page.html", "page.md", "page.storage.xml"]
    for kind, name in FILES.items():
        assert (folder / name).read_text(encoding="utf-8") == PAGE[kind]
        assert saved["files"][kind] == str(folder.resolve() / name)
    assert saved["bytes"] == sum(len(PAGE[k].encode("utf-8")) for k in FILES)


def test_comment_keeps_the_page_url_placeholder(records):
    saved = save(state(), records)
    assert open(saved["files"]["comment"], encoding="utf-8").read().endswith("Page: {page_url}")


@pytest.mark.skipif(os.name == "nt", reason="POSIX file modes")
def test_files_get_normal_permissions_not_private_ones(records):
    saved = save(state(), records)
    for path in saved["files"].values():
        assert os.stat(path).st_mode & 0o777 == save_local.FILE_MODE != 0o600


def test_no_temporary_files_are_left(records):
    save(state(), records)
    assert not [p for p in records.rglob("*") if p.name.endswith(".tmp")]


def test_saving_again_gives_identical_files_and_another_run_gets_its_own_folder(records):
    first = save(state(), records)
    again = save(state(), records)
    assert first == again
    other = save(state(run_id="20261111-130000-def456"), records)
    assert other["folder"] != first["folder"] and len(list((records / "SPEC-12").iterdir())) == 2


def test_unknown_ticket_goes_to_unknown(records):
    saved = save(state(ticket=None, ticket_ref="not a ticket"), records)
    assert saved["error"] == "" and "/unknown/20261111-120000-abc123" in saved["folder"].replace("\\", "/")


@pytest.mark.parametrize("run_id", ["../../etc", "..", "a/b", "", "x" * 65])
def test_unsafe_run_ids_are_refused_and_nothing_is_written(records, run_id):
    saved = save(state(run_id=run_id), records)
    assert saved["error"].startswith("not saved: unsafe run id") and saved["files"] == {}
    assert not records.exists() or not any(records.rglob("page.html"))


def test_no_page_writes_nothing(records):
    st = state()
    st.pop("page")
    saved = save(st, records)
    assert saved["error"] == "no page to save" and not records.exists()


@pytest.mark.skipif(os.name == "nt" or (hasattr(os, "geteuid") and os.geteuid() == 0),
                    reason="read-only folders need a non-root POSIX user")
def test_a_write_error_is_reported_not_raised(records):
    (records / "SPEC-12").mkdir(parents=True)
    os.chmod(records / "SPEC-12", 0o500)
    try:
        saved = save(state(), records)
    finally:
        os.chmod(records / "SPEC-12", 0o700)
    assert saved["error"].startswith("files could not be saved: PermissionError") and saved["files"] == {}


def test_a_failed_write_halfway_leaves_no_temporary_file(records, monkeypatch):
    real = os.replace
    calls = {"n": 0}

    def flaky(src, dst):
        calls["n"] += 1
        if calls["n"] == 2:
            raise OSError("disk full")
        return real(src, dst)
    monkeypatch.setattr(save_local.os, "replace", flaky)
    saved = save(state(), records)
    assert saved["error"] == "files could not be saved: OSError: disk full"
    assert not [p for p in records.rglob("*") if p.name.endswith(".tmp")]


def test_a_secret_that_slipped_through_is_redacted_with_a_warning(records):
    st = state()
    st["page"]["markdown"] = "Log in with password: Hunter2025!"
    saved = save(st, records)
    assert "Hunter2025!" not in open(saved["files"]["markdown"], encoding="utf-8").read()
    assert saved["warnings"] == ["page.md: 1 secret-like text(s) redacted before saving"]


def test_broken_storage_is_saved_with_a_warning(records):
    st = state()
    st["page"]["storage"] = "<p>not closed"
    saved = save(st, records)
    assert saved["files"] and saved["warnings"] == ["page.storage.xml is not well-formed XML, so publish must refuse it"]


# --- in the graph --------------------------------------------------------------------------------------

@pytest.mark.parametrize("mode", ["dry-run", "eval"])
def test_dry_run_and_eval_end_with_save_local_and_the_record_points_to_the_files(start, records, mode):
    r = start("SPEC-66", mode=mode)
    assert [t["node"] for t in r.state["trace"]][-2:] == ["render", "save_local"]
    saved = r.state["saved"]
    assert saved["error"] == "" and open(saved["files"]["html"], encoding="utf-8").read() == r.state["page"]["html"]
    rec = json.loads(r.record_path.read_text())
    assert rec["state"]["saved"] == saved and rec["mode"] == mode
    assert r.record_path.with_suffix("") == records / "SPEC-66" / r.run_id     # the folder sits next to the record


def test_a_write_error_in_the_graph_keeps_the_run_and_says_so(start, records, monkeypatch):
    def broken(path, text):
        raise OSError("read-only file system")
    monkeypatch.setattr(save_local, "write_atomic", broken)
    r = start("SPEC-66")
    assert r.status in ("complete", "incomplete") and "files could not be saved" in r.message
    rec = json.loads(r.record_path.read_text())
    assert rec["state"]["page"]["storage"] and "files could not be saved" in rec["note"]


def test_the_command_prints_the_saved_page(start, records, monkeypatch, capsys):
    from scripts import run_ticket as cli
    monkeypatch.setattr(cli, "run_ticket", lambda *a, **k: start("SPEC-66"))
    code = cli.main(["SPEC-66", "--no-preflight"])
    out = capsys.readouterr().out
    assert code == 0 and "saved:  " in out and "page.html" in out and "comment:" in out
