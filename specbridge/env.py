"""Settings from the project's .env file, with real environment variables taking priority."""
import os
import pathlib

PROJECT = pathlib.Path(__file__).resolve().parent.parent


def load_env(path=PROJECT / ".env", use_os=True):
    """Read KEY=VALUE lines (missing file -> empty). Environment variables override the file."""
    env = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                env[key.strip()] = value.strip().strip('"').strip("'")
    if use_os:
        env.update({k: v for k, v in os.environ.items() if k in env or k.startswith(("BRAIN", "OPENROUTER_", "EMBED_"))})
    return env
