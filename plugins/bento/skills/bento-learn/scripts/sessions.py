#!/usr/bin/env python3
"""Print the learnable part of every Claude and Codex session run in this worktree.

Usage: sessions.py [--repo PATH] [--since EPOCH_SECONDS]

Selects transcripts whose cwd is inside the worktree and that were active since the
current branch was created (its oldest reflog entry; else its merge-base with
origin/HEAD). Conductor-style workspaces reuse directories across branches, so the
time window matters as much as the path. For each session, oldest first, prints the
transcript path, then operator turns (U), failed tool calls (ERR) and blocking hook
errors (HOOK). Those are ~3% of transcript bytes and carry the Reflect signal; open
the printed path when a session needs more context.

A second pass adds sessions run from another directory (another workspace working here by
absolute path) whose transcript names the worktree path or one of the branch's names, old
names from `git branch -m` included. They print under "(other directory: <cwd>)".
"""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys

INJECTED = [re.compile(p, re.S) for p in (
    r"<(system_instruction|system-reminder|user-preferences|local-command-stdout|"
    r"environment_context|recommended_plugins|user_instructions)>.*?</\1>",
    r"# AGENTS\.md instructions for [^\n]*\s*<INSTRUCTIONS>.*?</INSTRUCTIONS>",
)]


def clean(text):
    for pattern in INJECTED:
        text = pattern.sub("", text)
    return text.strip()


def git(repo, *args):
    result = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True)
    return result.stdout.strip() if result.returncode == 0 else ""


def branch_start(repo):
    branch = git(repo, "symbolic-ref", "-q", "HEAD")
    reflog = git(repo, "reflog", "show", "--format=%ct", branch) if branch else ""
    if reflog:
        return int(reflog.splitlines()[-1])
    base = git(repo, "merge-base", "HEAD", "origin/HEAD")
    return int(git(repo, "show", "-s", "--format=%ct", base) or 0) if base else 0


def records(path):
    with path.open(errors="replace") as handle:
        for line in handle:
            try:
                record = json.loads(line)
            except ValueError:
                continue
            if isinstance(record, dict):
                yield record


def session_cwd(path):
    for record in records(path):
        cwd = record.get("cwd") or (record.get("payload") or {}).get("cwd")
        if cwd:
            return cwd
    return None


def signal(record):
    """Yield (tag, text) for one Claude or Codex transcript record."""
    kind, payload = record.get("type"), record.get("payload") or {}
    content = (record.get("message") or {}).get("content")
    if kind == "user" and not record.get("isMeta") and isinstance(content, str):
        yield "U", clean(content)[:2000]
    elif kind == "user" and isinstance(content, list):
        for item in content:
            if isinstance(item, dict) and item.get("type") == "tool_result" and item.get("is_error"):
                yield "ERR", str(item.get("content"))[:600]
    elif kind == "attachment" and (record.get("attachment") or {}).get("type") == "hook_blocking_error":
        yield "HOOK", str(record["attachment"])[:600]
    elif kind == "response_item" and payload.get("type") == "message" and payload.get("role") == "user":
        text = "\n".join(c.get("text", "") for c in payload.get("content") or []
                         if isinstance(c, dict) and c.get("type") == "input_text")
        yield "U", clean(text)[:2000]
    elif kind == "response_item" and payload.get("type") == "custom_tool_call_output":
        text = "\n".join(str(c.get("text", "")) for c in payload.get("output") or [] if isinstance(c, dict))
        if re.match(r"(Script failed|Script error:)", text):
            yield "ERR", text[:600]
    elif kind == "event_msg" and payload.get("type") == "item_completed":
        item = payload.get("item") or {}
        if item.get("status") == "failed":
            yield "ERR", str(item.get("aggregated_output") or item.get("stderr") or item)[:600]


def branch_names(repo):
    """The current branch's name plus every old name it had before a `git branch -m`."""
    branch = git(repo, "symbolic-ref", "-q", "--short", "HEAD")
    if not branch:
        return set()
    log = git(repo, "reflog", "show", "--format=%gs", branch)
    names = {branch, *re.findall(r"^Branch: renamed refs/heads/(\S+) to ", log, re.M)}
    # A renamed default branch would match nearly every transcript.
    return names - {"main", "master", git(repo, "rev-parse", "--abbrev-ref", "origin/HEAD")[len("origin/"):]}


def mentions(path, pattern):
    with path.open(errors="replace") as handle:
        return any(pattern.search(line) for line in handle)


def transcripts(root, since, names):
    """Yield (agent, path, None) for worktree sessions, then (agent, path, cwd) for sessions
    run elsewhere whose text names the worktree path or one of the branch's names."""
    claude = Path(os.environ.get("CLAUDE_CONFIG_DIR", Path.home() / ".claude")) / "projects"
    mangled = re.sub(r"[^A-Za-z0-9]", "-", str(root))
    found = [("claude", path) for folder in (claude.iterdir() if claude.is_dir() else [])
             for path in folder.glob("*.jsonl")]
    codex = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")) / "sessions"
    found += [("codex", path) for path in codex.glob("**/rollout-*.jsonl")]
    found = sorted((item for item in found if item[1].stat().st_mtime >= since),
                   key=lambda item: item[1].stat().st_mtime)
    other = []
    for agent, path in found:
        cwd = session_cwd(path)
        in_worktree = cwd and (cwd == str(root) or cwd.startswith(f"{root}/"))
        own_folder = agent == "codex" or path.parent.name == mangled or path.parent.name.startswith(mangled + "-")
        if in_worktree and own_folder:
            yield agent, path, None
        elif not in_worktree:
            other.append((agent, path, cwd))
    # Bounded so a sibling like <root>-other or a longer branch name does not match.
    pattern = re.compile(r"(?<![\w.-])(?:%s)(?![\w.-])" % "|".join(map(re.escape, [str(root), *names])))
    for agent, path, cwd in other:
        if mentions(path, pattern):
            yield agent, path, cwd or "?"


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--since", type=int, help="epoch seconds (default: branch creation)")
    args = parser.parse_args()
    root = git(args.repo, "rev-parse", "--show-toplevel")
    if not root:
        print(f"sessions.py: not a git worktree: {args.repo}", file=sys.stderr)
        return 1
    root = Path(root).resolve()
    since = branch_start(root) if args.since is None else args.since
    counts = {"in-worktree": 0, "other-directory": 0}
    for agent, path, cwd in transcripts(root, since, branch_names(root)):
        lines = [f"{tag}: {text}" for record in records(path) for tag, text in signal(record) if text]
        if any(line.startswith("U: ") for line in lines):
            counts["other-directory" if cwd else "in-worktree"] += 1
            where = f" (other directory: {cwd})" if cwd else ""
            print(f"=== {agent} session {path}{where}\n" + "\n".join(lines) + "\n")
    print(f"sessions.py: {counts['in-worktree']} in-worktree, {counts['other-directory']} other-directory session(s) "
          f"for {root} since {since}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
