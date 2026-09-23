#!/usr/bin/env python3
"""Bootstrap vendored plugins; print the durable principles root on stdout."""
import json
from pathlib import Path
import shutil
import subprocess
import sys


PLUGINS = ("bento-core@bento", "bento-forge@bento")
CLI_TIMEOUT = 300  # Local installs are fast; existing GitHub sources can need minutes.


def note(message):
    print(f"bento: {message}", file=sys.stderr)


def git(root, *args):
    return subprocess.check_output(
        ["git", "-C", str(root), *args], text=True, stderr=subprocess.DEVNULL
    ).strip()


def main_checkout(repo):
    # Git lists the main checkout first, including when called from a worktree.
    record = git(repo, "worktree", "list", "--porcelain", "-z").split("\0")[0]
    return Path(record.removeprefix("worktree ")).resolve()


def vendored_root(root):
    if root.name != ".bento":
        return None
    try:
        entry = git(root.parent, "ls-files", "--stage", "--", ".bento")
        if not entry.startswith("160000 "):
            return None
        stable = main_checkout(root.parent) / ".bento"
        if stable == root:
            return root
        if (not (stable / "install.sh").is_file()
                or Path(git(stable, "rev-parse", "--show-toplevel")).resolve() != stable):
            raise RuntimeError(
                f"initialize .bento in the main checkout ({stable.parent}) with "
                "git submodule update --init .bento, then rerun setup there."
            )
        if (git(stable, "rev-parse", "HEAD") != git(root, "rev-parse", "HEAD")
                or git(root, "status", "--porcelain")
                or git(stable, "status", "--porcelain")):
            raise RuntimeError(
                f"worktree and main-checkout .bento differ or have local changes. "
                f"Align their pins and use a clean {stable}, then rerun setup."
            )
        note(f"using main-checkout submodule {stable}; worktree paths are temporary")
        return stable
    except subprocess.CalledProcessError as exc:
        raise RuntimeError("cannot resolve the .bento submodule's main checkout") from exc


def claude(repo, *args, json_output=False):
    command = ["claude", "plugin", *args]
    if json_output:
        command.append("--json")
    try:
        result = subprocess.run(
            command, cwd=repo, stdin=subprocess.DEVNULL, capture_output=True,
            text=True, timeout=CLI_TIMEOUT, check=True,
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"{' '.join(command)} timed out after {CLI_TIMEOUT}s; rerun setup") from exc
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(f"{' '.join(command)} failed:\n{exc.stdout}{exc.stderr}") from exc
    if json_output:
        try:
            data = json.loads(result.stdout)
            if not isinstance(data, list) or not all(isinstance(row, dict) for row in data):
                raise ValueError("expected a JSON array of objects")
            return data
        except ValueError as exc:
            raise RuntimeError(f"cannot read {' '.join(command)}: {exc}") from exc
    note((result.stdout + result.stderr).strip())


def check_marketplace(marketplace):
    source = marketplace.get("source")
    location = marketplace.get("path") or marketplace.get("repo") or source
    note(f"keeping registered marketplace bento ({source}: {location})")
    if source != "directory":
        return
    path = Path(marketplace.get("path", "")).resolve()
    repair = "Run claude plugin marketplace remove bento, then rerun bash .bento/install.sh from a durable checkout."
    if not (path / ".claude-plugin/marketplace.json").is_file():
        raise RuntimeError(f"registered bento directory is missing: {path}. {repair}")
    try:
        repo = Path(git(path, "rev-parse", "--show-toplevel")).resolve()
        parent = git(repo, "rev-parse", "--show-superproject-working-tree")
        owner = Path(parent) if parent else repo
        if main_checkout(owner) != owner:
            raise RuntimeError(f"registered bento directory is in a temporary worktree: {path}. {repair}")
    except subprocess.CalledProcessError:
        pass  # A non-Git directory marketplace can also be a durable source.


def applicable(rows, plugin, repo):
    return [row for row in rows if row.get("id") == plugin and (
        row.get("scope") in ("user", "managed")
        or (row.get("projectPath") and Path(row["projectPath"]).resolve() == repo)
    )]


def installed(rows):
    return any(row.get("installPath") and Path(row["installPath"]).is_dir() for row in rows)


def bootstrap(root):
    stable = vendored_root(root)
    if stable is None:
        return root  # Marketplace/dev installs retain the principles-only behavior.
    if not shutil.which("claude"):
        raise RuntimeError("vendored setup requires the Claude Code CLI on PATH; install it and rerun bash .bento/install.sh")
    repo = root.parent
    marketplaces = claude(repo, "marketplace", "list", json_output=True)
    existing = next((row for row in marketplaces if row.get("name") == "bento"), None)
    if existing:
        check_marketplace(existing)
        claude(repo, "marketplace", "update", "bento")
    else:
        note(f"registering durable directory marketplace {stable}")
        claude(repo, "marketplace", "add", str(stable))
    rows = claude(repo, "list", json_output=True)
    for plugin in PLUGINS:
        matches = applicable(rows, plugin, repo)
        if not installed(matches):
            note(f"installing {plugin} at user scope (up to {CLI_TIMEOUT}s)")
            claude(repo, "install", plugin, "--scope", "user")
        else:
            # Versions are commit SHAs, so this picks up every merged change.
            for scope in sorted({row.get("scope") for row in matches} - {"managed", None}):
                claude(repo, "update", plugin, "--scope", scope)
        if installed(matches) and all(row.get("enabled") is True for row in matches):
            note(f"{plugin} already installed and enabled")
            continue
        # A project/local disable can override a new user installation.
        current = applicable(claude(repo, "list", json_output=True), plugin, repo)
        if not all(row.get("enabled") is True for row in current):
            claude(repo, "enable", plugin)
    markets = claude(repo, "marketplace", "list", json_output=True)
    rows = claude(repo, "list", json_output=True)
    if not any(row.get("name") == "bento" for row in markets):
        raise RuntimeError("bento marketplace registration is still missing; rerun setup")
    for plugin in PLUGINS:
        matches = applicable(rows, plugin, repo)
        if not installed(matches) or not all(row.get("enabled") is True for row in matches):
            raise RuntimeError(f"{plugin} is not installed and enabled in {repo}; inspect claude plugin list --json")
    note("both plugins installed, updated and enabled; restart Claude to load the skills")
    return stable


if __name__ == "__main__":
    try:
        print(bootstrap(Path(sys.argv[1]).resolve()))
    except (RuntimeError, OSError) as exc:
        note(str(exc))
        sys.exit(1)
