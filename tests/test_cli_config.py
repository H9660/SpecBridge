from typer.testing import CliRunner

from specbridge.cli import app
from specbridge.config import agent_model, judge_model, load_config, snapshots

COMMANDS = ["index", "run", "eval", "gate", "compare", "failures", "ui", "golden", "rate", "log", "customers"]


def test_help_lists_every_command():
    out = CliRunner().invoke(app, ["--help"]).output
    assert all(c in out for c in COMMANDS)


def test_stubs_exit_with_phase_message():
    result = CliRunner().invoke(app, ["gate", "some-run"])
    assert result.exit_code == 2 and "Phase 4" in result.output


def test_agent_model_honours_brain_switch():
    config = load_config()
    assert agent_model(config, env={}) == (config["models"]["agent"], None)
    assert agent_model(config, env={"BRAIN_MODEL": "google/gemini-4-argon"})[0] == "openrouter/google/gemini-4-argon"
    model, base = agent_model(config, env={"BRAIN": "slm"})
    assert model.startswith("ollama_chat/") and base.startswith("http://")


def test_judge_differs_from_agent_and_snapshots_pinned():
    config = load_config()
    assert judge_model(config) != config["models"]["agent"]
    pins = snapshots(config)
    assert len(pins) == 5 and all(len(sha) == 40 for sha in pins.values())
