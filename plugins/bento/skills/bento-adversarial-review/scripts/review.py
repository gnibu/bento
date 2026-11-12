#!/usr/bin/env python3
"""Run the other model family's CLI on a diff; leave the result in the git dir.

    review.py codex|claude [--model M] [--effort E] [--focus TEXT] (--uncommitted | [--] GIT_ARGS...)

GIT_ARGS is the scope command without its leading `git` (`diff origin/master...HEAD`,
`show <sha>`); --uncommitted is `git diff HEAD` plus untracked files. Files, all from
`git rev-parse --git-path`: adversarial-review.diff (the diff), .md (the findings), .log (the
reviewer's or git's output), and .exit, written last: `EXIT=<reviewer status>`, `EXIT=diff-failed`
or `EXIT=empty-diff`. Prints the .exit line, then the findings.

One plain command, so that an agent host never sees `rm` or a heredoc in its shell call: Claude
Code asks before such a command in every permission mode, Bypass included.

Python 3.9+ and Git; no third-party dependencies.
"""
import argparse
from pathlib import Path
import subprocess
import sys
from typing import IO, List

PROMPT = Path(__file__).with_name("prompt.md")
MODELS = {"codex": "gpt-6-astra", "claude": "opus"}


def git_path(name: str) -> Path:
    out = subprocess.run(["git", "rev-parse", "--git-path", name],
                         capture_output=True, text=True, check=True).stdout.strip()
    return Path(out).resolve()


def write_diff(scope: List[str], uncommitted: bool, diff: IO[bytes], log: IO[bytes]) -> bool:
    """Write the scope's diff; False when its git command fails."""
    if not uncommitted:
        return subprocess.run(["git", *scope], stdout=diff, stderr=log).returncode == 0
    if subprocess.run(["git", "diff", "HEAD"], stdout=diff, stderr=log).returncode:
        return False
    untracked = subprocess.run(["git", "ls-files", "-o", "--exclude-standard", "-z"],
                               capture_output=True, check=True).stdout
    for name in filter(None, untracked.split(b"\0")):
        # `--no-index` exits 1 on any difference: its status is dropped.
        subprocess.run(["git", "diff", "--no-index", "--", "/dev/null", name], stdout=diff, stderr=log)
    return True


def reviewer_cmd(args: argparse.Namespace, prompt: str, diff: Path, out: Path) -> List[str]:
    if args.reviewer == "codex":
        # Plain `codex exec`: `codex exec review` keeps a bug-only rubric.
        return ["codex", "exec", "-s", "read-only", "-m", args.model,
                "-c", f"model_reasoning_effort={args.effort}", "-o", str(out),
                f"The diff under review is in the file {diff}. {prompt}"]
    return ["claude", "-p", "--model", args.model, "--setting-sources", "", "--tools", "Read,Grep,Glob",
            "--strict-mcp-config", "--no-session-persistence", f"The diff under review is on stdin. {prompt}"]


def run_reviewer(args: argparse.Namespace, prompt: str, diff: Path, out: Path, log: IO[bytes]) -> int:
    cmd = reviewer_cmd(args, prompt, diff, out)
    try:
        if args.reviewer == "codex":  # stdin closed, or codex waits on it forever
            return subprocess.run(cmd, stdin=subprocess.DEVNULL, stdout=log, stderr=log).returncode
        with diff.open("rb") as stdin, out.open("wb") as findings:
            return subprocess.run(cmd, stdin=stdin, stdout=findings, stderr=log).returncode
    except FileNotFoundError as e:
        log.write(f"{e}\n".encode())
        return 127


def review(args: argparse.Namespace) -> str:
    d, x, o, l = (git_path(f"adversarial-review.{ext}") for ext in ("diff", "exit", "md", "log"))
    x.unlink(missing_ok=True)  # the caller polls for .exit: a stale one would end its wait now
    o.unlink(missing_ok=True)
    prompt = f"{PROMPT.read_text().strip()} {args.focus}".strip()
    with d.open("wb") as diff, l.open("wb") as log:
        ok = write_diff(args.scope, args.uncommitted, diff, log)
    if not ok:
        status = "diff-failed"
    elif d.stat().st_size == 0:
        status = "empty-diff"
    else:
        with l.open("wb") as log:
            status = str(run_reviewer(args, prompt, d, o, log))
    x.write_text(f"EXIT={status}\n")
    return status


def main(argv: List[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("reviewer", choices=sorted(MODELS))
    parser.add_argument("--model", help="default: gpt-6-astra for codex, opus for claude")
    parser.add_argument("--effort", default="high", help="codex model_reasoning_effort (default: high)")
    parser.add_argument("--focus", default="", help="what to focus on, appended to the prompt")
    parser.add_argument("--uncommitted", action="store_true", help="git diff HEAD plus untracked files")
    parser.add_argument("scope", nargs="*", help="the scope command's git arguments (after `--` if one starts with -)")
    # Everything after the first `--` is the scope, verbatim: argparse would drop a later `--`
    # (Python 3.9), turning `diff HEAD -- path` into a comparison with a revision named `path`.
    split = argv.index("--") if "--" in argv else len(argv)
    args = parser.parse_intermixed_args(argv[:split])
    args.scope += argv[split + 1:]
    if args.uncommitted == bool(args.scope):
        parser.error("give either --uncommitted or the scope command's git arguments")
    args.model = args.model or MODELS[args.reviewer]
    status = review(args)
    print(f"EXIT={status}")
    findings = git_path("adversarial-review.md")
    if findings.exists() and findings.read_text().strip():
        print(findings.read_text().rstrip("\n"))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
