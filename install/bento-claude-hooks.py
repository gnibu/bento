#!/usr/bin/env python3
"""Wire Claude hooks once per project, across worktrees (Python 3.9+)."""
import argparse
import os
from pathlib import Path
import shlex
import subprocess
import sys

from bento_hooks import hook_command, merge_json_hooks


def install(repo, config, scope="project", purge=False):
    repo = repo.resolve()
    command_factory = hook_command
    if scope == "personal":
        # All worktrees share a Git common directory. Guard user hooks to this repo.
        common = subprocess.check_output(
            ["git", "-C", str(repo), "rev-parse", "--git-common-dir"], text=True
        ).strip()
        identity = (repo / common).resolve()
        guard = (
            'bento_common="$(git rev-parse --git-common-dir 2>/dev/null)" || exit 0; '
            '[ "$(cd "$bento_common" && pwd -P)" = ' + shlex.quote(str(identity)) + ' ] || exit 0; '
        )
        command_factory = lambda: guard + hook_command()
        path = config / "settings.json"
    else:
        path = repo / ".claude/settings.json"
    if path.is_symlink() or path.parent.is_symlink():
        raise ValueError(f"refusing linked settings destination: {path}")
    before = path.read_text() if path.exists() else ""
    after = merge_json_hooks(before, purge, command_factory)
    if before == after:
        print("bento: no Claude hook changes needed")
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(after)
        action = "removed" if purge else "configured"
        print(f"bento: {action} Bento SessionStart hook in {path}")
    if scope == "project" and not purge:
        print("bento: commit .claude/settings.json so new worktrees inherit the hook")
    print("bento: start a fresh Claude session to apply hook changes")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, help="consumer repo (default: current Git root)")
    parser.add_argument("--scope", choices=("project", "personal"), default="project")
    parser.add_argument("--purge", action="store_true")
    args = parser.parse_args()
    try:
        repo = args.repo or Path(subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"], text=True).strip())
        config = Path(os.environ.get("CLAUDE_CONFIG_DIR", Path.home() / ".claude"))
        install(repo, config, args.scope, args.purge)
    except (ValueError, OSError, subprocess.CalledProcessError, AttributeError, TypeError) as exc:
        print(f"bento: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
