#!/usr/bin/env python3
"""Install relative native skill links and merge the Codex SessionStart hook (Python 3.11+)."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tomllib

from bento_hooks import hook_command, merge_json_hooks


START = "# bento:hooks:start"
END = "# bento:hooks:end"
CORE = ".bento/plugins/bento-core/skills"
FORGE = ".bento/plugins/bento-forge/skills"


def legacy_team_hooks(auto_pr):
    """The two generated hook commands from before Stop learning was removed."""
    start = hook_command()
    stop = start.replace("session-start.sh", "session-stop.sh")
    if auto_pr:
        stop = stop.replace('bash "$bento_hook"', 'BENTO_IMPROVE_AUTO_PR=1 bash "$bento_hook"')
    return {"hooks": {event: [{"hooks": [{"type": "command", "command": command,
                                             "timeout": 5}]}]
                      for event, command in (("SessionStart", start), ("Stop", stop))}}


def team_hooks(text, purge):
    tomllib.loads(text)  # Refuse malformed input before planning any writes.
    if text.count(START) != text.count(END) or text.count(START) > 1:
        raise ValueError("invalid bento hook markers in config.toml")
    pattern = re.compile(r"(?m)^" + re.escape(START) + r"\n.*?^" + re.escape(END) + r"\n?", re.S)
    if START in text and not pattern.search(text):
        raise ValueError("invalid bento hook block in config.toml")
    if START in text:
        existing = tomllib.loads(pattern.search(text).group())
        current = {"hooks": {"SessionStart": [{"hooks": [
            {"type": "command", "command": hook_command(), "timeout": 5}]}]}}
        if existing not in (current, legacy_team_hooks(False), legacy_team_hooks(True)):
            raise ValueError("Bento hook block was edited; move custom entries outside its markers before rerunning")
    block = ""
    if not purge:
        lines = [START, "[[hooks.SessionStart]]", "[[hooks.SessionStart.hooks]]", 'type = "command"',
                 "command = " + json.dumps(hook_command()), "timeout = 5", ""]
        block = "\n".join(lines) + END + "\n"
    if START in text:
        result = pattern.sub(lambda _: block, text)
    elif block:
        result = text + ("\n" if text and not text.endswith("\n") else "") + block
    else:
        result = text
    tomllib.loads(result)
    return result


def owned_link(path):
    if not path.is_symlink():
        return False
    target = os.readlink(path)
    # Exact relative targets remain identifiable even after submodule deinit/removal.
    return target in (f"../../{CORE}/{path.name}", f"../../{FORGE}/bento-improve") and (
        target.startswith(f"../../{CORE}/") or path.name == "bento-improve"
    )


def install(repo, codex_home, hooks="personal", purge=False):
    repo = repo.resolve()
    skills = repo / ".codex/skills"
    for directory in (repo / ".codex", skills):
        if directory.is_symlink() or (directory.exists() and not directory.is_dir()):
            raise ValueError(f"refusing linked/non-directory destination: {directory}")
    links = []
    removals = []
    if purge:
        if skills.is_dir():
            removals = sorted(path for path in skills.iterdir() if owned_link(path))
    else:
        source = repo / CORE
        if not source.is_dir():
            raise ValueError(f"initialize the vendored submodule first: {source}")
        targets = sorted(path for path in source.iterdir() if path.is_dir())
        targets.append(repo / FORGE / "bento-improve")
        names = set()
        for target in targets:
            if not (target / "SKILL.md").is_file():
                raise ValueError(f"missing SKILL.md: {target}")
            dest = skills / target.name
            relative = os.path.relpath(target, skills)
            if target.name in names:
                raise ValueError(f"duplicate skill name: {target.name}")
            names.add(target.name)
            if dest.is_symlink() and os.readlink(dest) == relative:
                continue
            if dest.is_symlink() or dest.exists():
                raise ValueError(f"skill collision at {dest}; move it yourself before installing")
            links.append((dest, relative))
    hook_path = None
    before = after = ""
    if hooks != "none":
        hook_path = codex_home / "hooks.json" if hooks == "personal" else repo / ".codex/config.toml"
        if hook_path.is_symlink():
            raise ValueError(f"refusing linked hook file: {hook_path}")
        before = hook_path.read_text() if hook_path.exists() else ""
        transform = merge_json_hooks if hooks == "personal" else team_hooks
        after = transform(before, purge)
    # All collisions and config parsing are checked before changing any files.
    for dest, relative in links:
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.symlink_to(relative, target_is_directory=True)
        print(f"bento: linked {dest} -> {relative}")
    for dest in removals:
        dest.unlink()
        print(f"bento: removed link {dest}")
    if after != before:
        hook_path.parent.mkdir(parents=True, exist_ok=True)
        hook_path.write_text(after)
        action = "removed" if purge else "configured"
        print(f"bento: {action} Bento SessionStart hook in {hook_path}")
    if not links and not removals and after == before:
        print("bento: no changes needed")
    print("bento: start a fresh Codex session to apply skill and hook changes")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, help="consumer repo (default: current Git root)")
    parser.add_argument("--hooks", choices=("personal", "team", "none"), default="personal")
    parser.add_argument("--purge", action="store_true", help="remove only Bento links and selected hooks")
    args = parser.parse_args()
    try:
        repo = args.repo or Path(subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"], text=True).strip())
        codex_home = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))
        install(repo, codex_home, args.hooks, args.purge)
    except (ValueError, OSError, subprocess.CalledProcessError, AttributeError, TypeError) as exc:
        print(f"bento: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
