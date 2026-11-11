"""Agent limits (ARCHITECTURE.md D9, D18, D19) from config/agent.json. A missing file means the defaults."""
import json
from dataclasses import dataclass, fields

from specbridge.env import PROJECT, load_env

CONFIG = PROJECT / "config" / "agent.json"


class SettingsError(ValueError):
    pass


@dataclass(frozen=True)
class Settings:
    cost_cap_usd: float = 0.25
    max_rounds: int = 2               # the first run plus 1 retry
    time_cap_seconds: float = 600
    max_tool_calls_per_round: int = 8
    reserve_share: float = 0.2
    max_workers: int = 5
    max_concurrency: int = 5

    @property
    def recursion_limit(self):
        # supersteps: intake, understand, clarify/render, publish + about 4 per round (orchestrator, workers, merge, reviewer)
        return 10 + 6 * self.max_rounds


RULES = {   # name: (types, smallest allowed, largest allowed or None, smallest is excluded)
    "cost_cap_usd": ((int, float), 0, None, True),
    "max_rounds": ((int,), 1, None, False),
    "time_cap_seconds": ((int, float), 0, None, True),
    "max_tool_calls_per_round": ((int,), 1, None, False),
    "reserve_share": ((int, float), 0, 0.9, False),
    "max_workers": ((int,), 1, None, False),
    "max_concurrency": ((int,), 1, None, False),
}


def _check(name, value):
    types, low, high, exclusive = RULES[name]
    if isinstance(value, bool) or not isinstance(value, types):
        raise SettingsError(f"{name} must be a number, not {value!r} (config/agent.json)")
    if value < low or (exclusive and value == low) or (high is not None and value > high):
        bound = f"above {low}" if exclusive else f"at least {low}"
        raise SettingsError(f"{name} must be {bound}" + (f" and at most {high}" if high is not None else "")
                            + f", not {value} (config/agent.json)")
    return value


def load_settings(env=None, config_path=CONFIG):
    env = load_env() if env is None else env
    if not config_path.exists():
        return Settings()
    try:
        raw = json.loads(config_path.read_text(encoding="utf-8"))
    except ValueError as err:
        raise SettingsError(f"{config_path.name} is not valid JSON: {err}") from None
    if not isinstance(raw, dict):
        raise SettingsError(f"{config_path.name} must hold one JSON object")
    known = {f.name for f in fields(Settings)}
    unknown = sorted(set(raw) - known - {"note"})
    if unknown:
        raise SettingsError(f"unknown setting(s) {unknown} in {config_path.name}; known: {sorted(known)}")
    values = {k: v for k, v in raw.items() if k in known}
    if isinstance(values.get("max_concurrency"), dict):   # one value per brain
        brain = env.get("BRAIN") or "llm"
        values["max_concurrency"] = values["max_concurrency"].get(brain, Settings.max_concurrency)
    return Settings(**{k: _check(k, v) for k, v in values.items()})
