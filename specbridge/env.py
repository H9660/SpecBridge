"""Settings from the project's .env file, with real environment variables taking priority."""
import os
import pathlib
import ssl
import sys

PROJECT = pathlib.Path(__file__).resolve().parent.parent


def is_certificate_error(err):
    """True if a failed connection was a certificate check, not the network (urllib wraps it in URLError)."""
    reason = getattr(err, "reason", err)
    return isinstance(reason, ssl.SSLCertVerificationError) or "CERTIFICATE_VERIFY_FAILED" in str(reason)


def network_hint(err):
    """What to do about a failed connection. A certificate error almost always means this Python has no trusted
    certificates (e.g. MSYS2's Python on Windows with no CA bundle), so the advice names the Python in use."""
    if is_certificate_error(err):
        return (f"this Python ({sys.executable}) cannot check website certificates; run SpecBridge with the project "
                "venv (.venv\\Scripts\\python on Windows, .venv/bin/python on Linux), or on a network that inspects "
                "HTTPS set SSL_CERT_FILE to its root certificate")
    return "check the internet connection"


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
        env.update({k: v for k, v in os.environ.items() if k in env or k.startswith(("BRAIN", "GEMINI_", "EMBED_", "SLM_"))})
    return env
