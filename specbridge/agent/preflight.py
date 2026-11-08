"""Brain check at START: is the AI brain set up and reachable, before any work is done?

Offline: the brain profile exists and its API key is set (load_brain). Online (one free call each,
no question is sent to the model): the key is accepted, its spending limit is not used up, and the
model is offered. Messages never contain the key.
"""
import json
import urllib.error
import urllib.request

from specbridge.brain import BrainError, load_brain


class PreflightError(RuntimeError):
    pass


class HTTPStatus(Exception):
    def __init__(self, code):
        super().__init__(code)
        self.code = code


def fetch_json(url, headers, timeout=20):
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as err:
        raise HTTPStatus(err.code) from None


def check_brain(env=None, network=True, fetch=fetch_json):
    """{brain, provider, model, network_checked, key_limit_remaining, credit_remaining, warnings}, or PreflightError."""
    try:
        brain = load_brain(env=env)
    except (BrainError, OSError, ValueError) as err:
        raise PreflightError(str(err)) from None
    info = {"brain": brain.name, "provider": brain.provider, "model": brain.model, "network_checked": network,
            "key_limit_remaining": None, "credit_remaining": None, "warnings": []}
    if not network:
        return info
    auth = {"Authorization": f"Bearer {brain._api_key}"} if brain._api_key else {}
    try:
        if brain.provider == "openrouter":
            _check_openrouter_key(brain, auth, fetch, info)
        ids = {m.get("id") for m in fetch(f"{brain.base_url}/models", auth).get("data", [])}
    except HTTPStatus as err:
        raise PreflightError(f"{brain.provider} answered HTTP {err.code} at {brain.base_url}; try again later") from None
    except (urllib.error.URLError, TimeoutError, OSError) as err:
        raise PreflightError(f"cannot reach {brain.provider} at {brain.base_url} ({_reason(err)}); "
                             "check the internet connection, or use --no-preflight for offline work") from None
    if brain.model not in ids:
        where = "pull it with `ollama pull`" if brain.provider == "ollama" else "check BRAIN_MODEL / config/brains.json"
        raise PreflightError(f"model {brain.model!r} is not offered by {brain.provider}; {where}")
    return info


def _check_openrouter_key(brain, auth, fetch, info):
    try:
        data = fetch(f"{brain.base_url}/key", auth).get("data") or {}
    except HTTPStatus as err:
        if err.code in (401, 403):
            raise PreflightError("OpenRouter rejected OPENROUTER_API_KEY (invalid, revoked or disabled); "
                                 "create a new key at https://openrouter.ai/settings/keys") from None
        raise
    remaining = data.get("limit_remaining")
    info["key_limit_remaining"] = remaining
    if remaining is not None and remaining <= 0:
        raise PreflightError(f"the OpenRouter key's spending limit is used up "
                             f"(limit ${data.get('limit')}, remaining ${remaining}); raise it at https://openrouter.ai/settings/keys")
    try:   # account balance: only a warning, since calls through the team's own Gemini key (BYOK) can still work
        credits = fetch(f"{brain.base_url}/credits", auth).get("data") or {}
        balance = credits.get("total_credits", 0) - credits.get("total_usage", 0)
        info["credit_remaining"] = round(balance, 4)
        if balance <= 0:
            info["warnings"].append(f"OpenRouter account credit is ${balance:.2f}; only calls through your own "
                                    "provider key (BYOK) will work")
    except HTTPStatus:
        info["warnings"].append("could not read the OpenRouter account credit")


def _reason(err):
    return getattr(err, "reason", None) or type(err).__name__
