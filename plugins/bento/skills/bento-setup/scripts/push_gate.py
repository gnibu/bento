#!/usr/bin/env python3
"""Pre-PR review gate: a PreToolUse hook (Claude Code and Codex) on shell commands.

Blocks `git push` and `gh pr create` unless bento-adversarial-review's recorded sha
(`git rev-parse --git-path adversarial-review.head`) is HEAD, or is followed only by that
review's own fix commits. Allowed without a record when the repo's bento-ship overlay says
`- Pre-PR review: skip`, or the command carries `BENTO_PRE_PR_REVIEW=skip` (a review the
user skipped for this run). Not a repo, unreadable input or an unparsable command → allow:
this gate catches a skipped ship flow, it is not a security boundary.

Usage:
  push_gate.py                                  hook: tool-call JSON on stdin, exit 2 blocks
  push_gate.py install <hooks.json> [--matcher Bash]
  push_gate.py uninstall <hooks.json>
"""
import json
import os
import re
import shlex
import subprocess
import sys
from pathlib import Path

MESSAGE = "Run bento-ship first: no pre-PR review recorded for HEAD."
BYPASS = "BENTO_PRE_PR_REVIEW=skip"
FIX_SUBJECT = "fix: address adversarial review findings"  # bento-adversarial-review ship mode
GIT_ARG_OPTS = {"-C", "-c", "--git-dir", "--work-tree", "--namespace"}


def gated_dirs(command: str, cwd: str) -> list[str]:
    """The directory of each `git push` / `gh pr create` in a shell command, following `cd`."""
    lex = shlex.shlex(command, posix=True, punctuation_chars=True)
    lex.whitespace_split = True
    try:
        tokens = list(lex)
    except ValueError:  # unbalanced quotes, e.g. an apostrophe in a heredoc: match the raw text
        if BYPASS in command:
            return []
        return [cwd] if re.search(r"\bgit(\s+-\S+)*\s+push\b|\bgh\s+pr\s+create\b", command) else []
    if BYPASS in tokens:
        return []
    out, here = [], cwd
    for i, tok in enumerate(tokens):
        if tok == "cd" and i + 1 < len(tokens):
            here = os.path.join(here, os.path.expanduser(tokens[i + 1]))
        elif os.path.basename(tok) == "git":
            repo, j = here, i + 1
            while j < len(tokens) and tokens[j].startswith("-"):
                if tokens[j] == "-C" and j + 1 < len(tokens):
                    repo = os.path.join(here, tokens[j + 1])
                j += 2 if tokens[j] in GIT_ARG_OPTS else 1
            if j < len(tokens) and tokens[j] == "push":
                out.append(repo)
        elif tok == "gh" and tokens[i + 1:i + 3] == ["pr", "create"]:
            out.append(here)
    return out


def reviewed(repo: str) -> bool:
    """True when HEAD needs no further pre-PR review before it leaves this machine."""
    def git(*args: str) -> subprocess.CompletedProcess:
        return subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True)

    top = git("rev-parse", "--show-toplevel")
    if top.returncode:
        return True  # not a repo: nothing to push
    overlay = Path(top.stdout.strip(), ".agents/bento/bento-ship.md")
    if overlay.is_file() and re.search(r"^- Pre-PR review:\s*skip\s*$", overlay.read_text(), re.M | re.I):
        return True
    try:
        sha = Path(repo, git("rev-parse", "--git-path", "adversarial-review.head").stdout.strip()).read_text().strip()
    except OSError:
        return False
    head = git("rev-parse", "HEAD").stdout.strip()
    recorded = git("rev-parse", "--verify", "--quiet", f"{sha}^{{commit}}").stdout.strip()
    if not recorded or recorded == head:
        return bool(recorded)
    if git("merge-base", "--is-ancestor", recorded, "HEAD").returncode:
        return False
    # Fix commits the review made after its recorded sha were triaged from its own findings.
    log = git("log", "--format=%P%x09%s", f"{recorded}..HEAD").stdout.splitlines()
    return all(" " not in parents and subject == FIX_SUBJECT
               for parents, _, subject in (line.partition("\t") for line in log))


def hook() -> int:
    try:
        event = json.load(sys.stdin)
        command = event.get("tool_input", {}).get("command")
        if isinstance(command, list):  # an argv, e.g. ["bash", "-lc", "git push"]
            command = " ".join(command)
        dirs = gated_dirs(command, event.get("cwd") or os.getcwd()) if isinstance(command, str) else []
    except (ValueError, AttributeError):  # not a tool-call JSON
        return 0
    if all(reviewed(d) for d in dirs):
        return 0
    print(MESSAGE, file=sys.stderr)
    return 2


def ours(group: dict) -> bool:
    return any("push_gate.py" in h.get("command", "") for h in group.get("hooks", []))


def hook_command() -> str:
    """This script, repo-relative when it lives in the current repo (project scope), else absolute."""
    script = Path(__file__).resolve()
    top = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True).stdout.strip()
    if top and script.is_relative_to(Path(top).resolve()):
        rel = script.relative_to(Path(top).resolve())
        path = f'"${{CLAUDE_PROJECT_DIR:-$(git rev-parse --show-toplevel)}}/{rel}"'
    else:
        path = shlex.quote(str(script))
    # A missing script must not block: python3 exits 2 (= block) on a file it can't open.
    return f"f={path}; [ ! -f \"$f\" ] || python3 \"$f\""


def edit(path: Path, change) -> str:
    text = path.read_text() if path.exists() else ""
    data = json.loads(text) if text.strip() else {}
    groups = data.setdefault("hooks", {}).setdefault("PreToolUse", [])
    action = change(groups)
    if not groups:
        del data["hooks"]["PreToolUse"]
    if not data["hooks"]:
        del data["hooks"]
    if action != "unchanged":
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2) + "\n")
    return action


def install(path: Path, matcher: str | None = None) -> str:
    entry: dict = {"matcher": matcher} if matcher else {}
    entry["hooks"] = [{"type": "command", "command": hook_command()}]

    def change(groups: list) -> str:
        old = [g for g in groups if ours(g)]
        if old == [entry]:
            return "unchanged"
        groups[:] = [g for g in groups if not ours(g)] + [entry]
        return "updated" if old else "added"
    return edit(path, change)


def uninstall(path: Path) -> str:
    def change(groups: list) -> str:
        kept = [g for g in groups if not ours(g)]
        action = "removed" if len(kept) < len(groups) else "unchanged"
        groups[:] = kept
        return action
    return edit(path, change) if path.exists() else "unchanged"


def main() -> int:
    args = sys.argv[1:]
    if not args:
        return hook()
    if args[0] == "install" and len(args) in (2, 4) and args[2:3] in ([], ["--matcher"]):
        print(f"bento: {install(Path(args[1]), args[3] if len(args) == 4 else None)} pre-PR review gate in {args[1]}")
        return 0
    if args[0] == "uninstall" and len(args) == 2:
        print(f"bento: {uninstall(Path(args[1]))} pre-PR review gate in {args[1]}")
        return 0
    print(__doc__, file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
