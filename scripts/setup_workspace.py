"""Download the repos in config/repos.json and set each one to its frozen "before" version.

Each repo gets full commit history (file contents are fetched only when needed) and a local
branch called `snapshot` pointing at the commit in data/snapshots.json. Safe to re-run.

Usage:
  py -3.12 scripts/setup_workspace.py [--workdir C:/specbridge-work]
"""
import argparse
import json
import pathlib
import subprocess

PROJECT = pathlib.Path(__file__).resolve().parent.parent
DEFAULT_WORKDIR = pathlib.Path("C:/specbridge-work")


def git(*args, cwd=None):
    return subprocess.run(["git", "-c", "core.longpaths=true", *args], cwd=cwd, check=True,
                          capture_output=True, text=True, encoding="utf-8").stdout


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--workdir", type=pathlib.Path, default=DEFAULT_WORKDIR,
                        help="where repos are downloaded (keep it outside OneDrive)")
    args = parser.parse_args()
    if "onedrive" in str(args.workdir.resolve()).lower():
        raise SystemExit(f"{args.workdir} is inside OneDrive; pick a folder outside it")
    args.workdir.mkdir(parents=True, exist_ok=True)

    config = json.loads((PROJECT / "config" / "repos.json").read_text(encoding="utf-8"))
    snapshots = json.loads((PROJECT / "data" / "snapshots.json").read_text(encoding="utf-8"))["repos"]

    for repo in config["repos"]:
        name, path = repo["name"], args.workdir / repo["name"]
        commit = snapshots[name]["commit"]
        if not (path / ".git").exists():
            print(f"{name}: downloading...")
            git("clone", "-q", "--filter=blob:none", "--no-checkout", repo["url"], str(path))
        else:
            git("fetch", "-q", "origin", cwd=path)
        git("config", "core.longpaths", "true", cwd=path)
        git("checkout", "-q", "-B", "snapshot", commit, cwd=path)
        files = len(git("ls-files", cwd=path).splitlines())
        print(f"{name}: on snapshot {commit[:10]} ({snapshots[name]['date']}), {files} files")


if __name__ == "__main__":
    main()
