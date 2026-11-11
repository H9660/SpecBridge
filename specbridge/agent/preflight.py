"""Brain check at START: is the AI brain set up and reachable, before any work is done?

Offline: the brain profile exists and its API key is set (load_brain). Online (one free call, no
question is sent to the model): the provider accepts the key and offers the model. Messages never
contain the key.
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


KEY_PAGES = {"google": "https://aistudio.google.com/apikey"}


def check_brain(env=None, network=True, fetch=fetch_json):
    """{brain, provider, model, network_checked, warnings}, or PreflightError."""
    try:
        brain = load_brain(env=env)
    except (BrainError, OSError, ValueError) as err:
        raise PreflightError(str(err)) from None
    info = {"brain": brain.name, "provider": brain.provider, "model": brain.model, "network_checked": network,
            "warnings": []}
    if brain.profile.get("price_usd_per_mtok"):
        info["warnings"].append(f"{brain.provider} does not report cost; costs shown are estimates at list price "
                                "(the free tier costs $0)")
    if not network:
        return info
    auth = {"Authorization": f"Bearer {brain._api_key}"} if brain._api_key else {}
    try:
        models = fetch(f"{brain.base_url}/models", auth).get("data", [])
    except HTTPStatus as err:
        if err.code in (400, 401, 403) and brain.profile.get("api_key_env"):   # Google answers a bad key with 400
            page = KEY_PAGES.get(brain.provider, "the provider's settings")
            raise PreflightError(f"{brain.provider} rejected {brain.profile['api_key_env']} (invalid, revoked or "
                                 f"restricted); create a new key at {page}") from None
        raise PreflightError(f"{brain.provider} answered HTTP {err.code} at {brain.base_url}; try again later") from None
    except (urllib.error.URLError, TimeoutError, OSError) as err:
        raise PreflightError(f"cannot reach {brain.provider} at {brain.base_url} ({_reason(err)}); "
                             "check the internet connection, or use --no-preflight for offline work") from None
    ids = {(m.get("id") or "").removeprefix("models/") for m in models}
    if brain.model not in ids:
        where = "pull it with `ollama pull`" if brain.provider == "ollama" else "check BRAIN_MODEL / config/brains.json"
        raise PreflightError(f"model {brain.model!r} is not offered by {brain.provider}; {where}")
    return info


def _reason(err):
    return getattr(err, "reason", None) or type(err).__name__


def check_atlassian(env=None, network=True, client_factory=None):
    """Live mode only, before any AI call: the Atlassian settings are set and (online) the Confluence space can be
    read with them. Returns {"site", "space", "network_checked"}; raises PreflightError otherwise."""
    from specbridge.atlassian import Atlassian, missing_settings
    from specbridge.env import load_env
    env = load_env() if env is None else env
    missing = missing_settings(env)
    if missing:
        raise PreflightError(f"live mode needs these settings in .env: {', '.join(missing)}")
    info = {"site": env["ATLASSIAN_SITE"].rstrip("/"), "space": env["CONFLUENCE_SPACE_KEY"], "network_checked": network}
    if not network:
        return info
    client = (client_factory or Atlassian)(env)
    try:
        space = client.confluence_space()
    except Exception as err:  # noqa: BLE001 - any failure here means publishing would fail too
        raise PreflightError(f"cannot read Confluence space {info['space']} at {info['site']}: "
                             f"{str(err)[:200]}") from None
    if not space:
        raise PreflightError(f"Confluence space {info['space']} was not found at {info['site']}")
    return info
