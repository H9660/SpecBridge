"""List project files that docs/repo_map.md does not mention, so the map can be kept up to date.

Usage:
  py -3.12 scripts/check_repo_map.py
"""
import pathlib
import subprocess

PROJECT = pathlib.Path(__file__).resolve().parent.parent
MAP = PROJECT / "docs" / "repo_map.md"


def main():
    files = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard"], cwd=PROJECT,
                           capture_output=True, text=True, encoding="utf-8", check=True).stdout.splitlines()
    text = MAP.read_text(encoding="utf-8")
    # data/retrieval/<method>.md|json are covered by one row
    missing = [f for f in files if pathlib.Path(f).name not in text and not f.startswith(("data/retrieval/", "data/understand/"))]
    if missing:
        print("Missing from docs/repo_map.md:\n  " + "\n  ".join(missing))
        raise SystemExit(1)
    print(f"docs/repo_map.md covers all {len(files)} project files")


if __name__ == "__main__":
    main()
