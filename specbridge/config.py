"""Project settings from config/config.yaml, plus the brain choice (BRAIN / BRAIN_MODEL) from .env."""
import json

import yaml

from specbridge.env import PROJECT, load_env

CONFIG_FILE = PROJECT / "config" / "config.yaml"
BRAINS_FILE = PROJECT / "config" / "brains.json"


def load_config(path=CONFIG_FILE):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def agent_model(config=None, env=None, brains_path=BRAINS_FILE):
    """(LiteLLM model id, api_base or None) for the agent.

    BRAIN_MODEL overrides everything (an OpenRouter id like google/gemini-4-argon). BRAIN=slm uses the local
    Ollama profile in config/brains.json. Otherwise the agent model from config.yaml.
    """
    config = load_config() if config is None else config
    env = load_env() if env is None else env
    brains = json.loads(brains_path.read_text(encoding="utf-8"))
    name = env.get("BRAIN") or brains["default"]
    profile = brains["brains"].get(name)
    if profile is None:
        raise ValueError(f"unknown brain '{name}'; choose one of {sorted(brains['brains'])} (config/brains.json)")
    if profile["provider"] == "ollama":
        model = env.get("BRAIN_MODEL") or profile["model"]
        return f"ollama_chat/{model}", profile["base_url"].removesuffix("/v1")
    if env.get("BRAIN_MODEL"):
        return f"{profile['provider']}/{env['BRAIN_MODEL']}", None
    return config["models"]["agent"], None


def judge_model(config=None):
    config = load_config() if config is None else config
    return config["models"]["judge"]


def snapshots(config=None):
    """{repo name: pinned commit} from the single source of truth named in config.yaml."""
    config = load_config() if config is None else config
    data = json.loads((PROJECT / config["target"]["snapshots_file"]).read_text(encoding="utf-8"))
    return {name: info["commit"] for name, info in data["repos"].items()}
