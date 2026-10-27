"""SpecBridge command line. Phase 0: every command exists; each stub names the phase that implements it."""
from pathlib import Path
from typing import Annotated

import typer

app = typer.Typer(help="SpecBridge: ticket in, code-grounded UAT test cases out, for PM review.",
                  no_args_is_help=True)
golden_app = typer.Typer(help="Golden set: validate drafts, freeze a version, import customer tickets.",
                         no_args_is_help=True)
rate_app = typer.Typer(help="Human ratings: export blind sheets, import them and compute agreement.",
                       no_args_is_help=True)
log_app = typer.Typer(help="Iteration log helper (docs/iteration_log.md).", no_args_is_help=True)
customers_app = typer.Typer(help="Customer session evidence.", no_args_is_help=True)
app.add_typer(golden_app, name="golden")
app.add_typer(rate_app, name="rate")
app.add_typer(log_app, name="log")
app.add_typer(customers_app, name="customers")

Variant = typer.Option("B_specbridge", help="A_baseline or B_specbridge.")


def _todo(phase, what):
    typer.secho(f"Not built yet: {what} (Phase {phase}, SPECBRIDGE_HANDOFF.md §12).", fg=typer.colors.YELLOW, err=True)
    raise typer.Exit(2)


@app.command()
def index(force: Annotated[bool, typer.Option(help="Rebuild even if the pinned commits are unchanged.")] = False):
    """Index the pinned repos: pieces, routes, symbol table, embeddings."""
    _todo(1, "index")


@app.command()
def run(ticket: Annotated[Path, typer.Option(help="Ticket JSON file.")], variant: str = Variant,
        out: Annotated[Path | None, typer.Option(help="Write the UATPage JSON and Markdown here.")] = None):
    """Generate a UAT page for one ticket."""
    _todo("2 (A_baseline) / 3 (B_specbridge)", "run")


@app.command("eval")
def eval_(golden: Annotated[str, typer.Option(help="Frozen golden version, e.g. v1.")] = "v1",
          variant: str = Variant,
          repeats: Annotated[int, typer.Option(help="Run each pair N times.")] = 1,
          subset: Annotated[str | None, typer.Option(help="Comma-separated pair IDs.")] = None,
          drafts: Annotated[bool, typer.Option(help="Run on golden/drafts (not a frozen version).")] = False):
    """Run the golden set and write a run folder under runs/."""
    _todo(4, "eval")


@app.command()
def gate(run_id: str):
    """Check a run against docs/ship_gate.yaml (prints GATE NOT DEFINED while any threshold is null)."""
    _todo(4, "gate")


@app.command()
def compare(run_a: str, run_b: str,
            allow_version_mismatch: Annotated[bool, typer.Option(help="Compare runs on different golden versions.")]
            = False):
    """Delta table and per-pair flips between two runs."""
    _todo(4, "compare")


@app.command()
def failures(run_id: str):
    """List failing pairs and draft runs/<run_id>/failure_clusters.md."""
    _todo(5, "failures")


@app.command()
def ui():
    """Start the Streamlit app (Review mode and Customer session mode)."""
    _todo(6, "ui")


@golden_app.command("validate")
def golden_validate(path: Path = Path("golden/drafts")):
    """Check schema, unique IDs, AC references and the 5:3:2 mix."""
    _todo(4, "golden validate")


@golden_app.command("freeze")
def golden_freeze(from_: Annotated[Path, typer.Option("--from", help="Drafts folder.")] = Path("golden/drafts"),
                  version: Annotated[str, typer.Option(help="New version name, e.g. v1.")] = "v1"):
    """Copy drafts into golden/<version>/ and write MANIFEST.json. Refuses if the version exists."""
    _todo(4, "golden freeze")


@golden_app.command("import-session")
def golden_import_session(file: Path):
    """Promote a customer-session ticket into golden/drafts/ (future versions only)."""
    _todo(6, "golden import-session")


@rate_app.command("export")
def rate_export(run_id: str, sample: int = 15, raters: int = 2):
    """Write blind rating sheets (no judge verdicts) for a stratified sample."""
    _todo(5, "rate export")


@rate_app.command("import")
def rate_import(run_id: str):
    """Read completed sheets: inter-rater κ, disagreement log, judge–human agreement."""
    _todo(5, "rate import")


@log_app.command("new")
def log_new(run: Annotated[str, typer.Option(help="Run ID.")],
            prev: Annotated[str | None, typer.Option(help="Previous run ID.")] = None):
    """Append a pre-filled iteration entry to docs/iteration_log.md."""
    _todo(5, "log new")


@customers_app.command("summary")
def customers_summary():
    """Aggregate customer sessions into customer/summary.md."""
    _todo(6, "customers summary")


if __name__ == "__main__":
    app()
