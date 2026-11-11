"""Start the SpecBridge service behind the Jira "Run SpecBridge" button (ADR D28, docs/DEPLOY_JIRA.md).

Usage:
  .venv/bin/python scripts/serve.py                 # live: the button publishes the page and comments on the ticket
  .venv/bin/python scripts/serve.py --dry-run       # try the service: runs save the page locally, nothing in Jira
Options: --host 127.0.0.1 (default; reachable from Jira only through a tunnel), --port 8765, --no-preflight.
Then expose it, e.g.:  cloudflared tunnel --url http://localhost:8765   and put that https address in the Jira rule.
Stop with Ctrl-C (a run in progress is stopped and queued again at the next start).
"""
import argparse
import logging
import pathlib
import sys
import urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from specbridge import service  # noqa: E402
from specbridge.agent import preflight  # noqa: E402
from specbridge.agent.limits import SettingsError, load_settings  # noqa: E402
from specbridge.env import load_env  # noqa: E402


def ollama_running():
    try:
        with urllib.request.urlopen("http://127.0.0.1:11434/api/tags", timeout=3):
            return True
    except Exception:  # noqa: BLE001
        return False


def make_parser():
    parser = argparse.ArgumentParser(description="Serve the Jira 'Run SpecBridge' button.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--dry-run", action="store_true", help="save pages locally; write nothing to Jira")
    parser.add_argument("--no-preflight", action="store_true", help="skip the online checks of Gemini and Atlassian")
    return parser


def main(argv=None):
    args = make_parser().parse_args(argv)

    service.STATE_DIR.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s",
                        handlers=[logging.StreamHandler(), logging.FileHandler(service.STATE_DIR / "service.log")])
    env = load_env()
    try:
        settings = load_settings(env)
        svc = service.Service(env, settings, dry_run=args.dry_run)
        brain = preflight.check_brain(env=env, network=not args.no_preflight)
        if not args.dry_run:
            preflight.check_atlassian(env=env, network=not args.no_preflight)
    except (service.ServiceError, SettingsError, preflight.PreflightError) as err:
        print(f"not started: {err}")
        return 2
    if not ollama_running():
        print("warning: Ollama is not running at 127.0.0.1:11434, so code search falls back to keywords only")
    if args.host not in ("127.0.0.1", "localhost"):
        print(f"warning: listening on {args.host}: other machines can reach the service directly (the secret still "
              "protects /run)")
    try:
        server = service.make_server(svc, args.host, args.port)
    except OSError as err:
        print(f"not started: cannot listen on {args.host}:{args.port} ({err})")
        return 2
    svc.start()
    print(f"SpecBridge service ({svc.mode}) on http://{args.host}:{args.port}  brain: {brain['model']}  "
          f"daily limit: ${settings.daily_budget_usd:.2f}  queued from last time: {len(svc.queue)}")
    print(f"next: cloudflared tunnel --url http://localhost:{args.port}   then use https://<address>/run in the Jira rule")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nstopping")
    finally:
        svc.stop()
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
