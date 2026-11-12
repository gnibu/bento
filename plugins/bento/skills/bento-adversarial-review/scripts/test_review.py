"""Run review.py against real Git repos, with stand-in codex and claude CLIs."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).with_name("review.py")

# Records its argv and stdin, writes findings where the real CLI would, exits with $FAKE_RC.
FAKE = """#!/usr/bin/env python3
import json, os, sys
args = sys.argv[1:]
stdin = "" if sys.stdin is None else sys.stdin.read()
with open(os.environ["FAKE_CALLS"], "a") as f:
    f.write(json.dumps({"cli": os.path.basename(sys.argv[0]), "args": args, "stdin": stdin}) + "\\n")
if "-o" in args:
    open(args[args.index("-o") + 1], "w").write("- [P2] codex finding\\n")
else:
    print("- [P2] claude finding")
print("trace", file=sys.stderr)
sys.exit(int(os.environ.get("FAKE_RC", "0")))
"""


class ReviewTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix="bento-review-test-")
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        self.repo, bin_dir = root / "repo with spaces", root / "bin"
        self.repo.mkdir()
        bin_dir.mkdir()
        for cli in ("codex", "claude"):
            (bin_dir / cli).write_text(FAKE)
            (bin_dir / cli).chmod(0o755)
        self.calls = root / "calls.jsonl"
        self.env = {**os.environ, "PATH": f"{bin_dir}{os.pathsep}{os.environ['PATH']}",
                    "FAKE_CALLS": str(self.calls)}
        self.git("init", "-q", "-b", "main")
        self.commit("app.py", "print('a')\n")

    def git(self, *args):
        return subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", *args], cwd=self.repo,
                              capture_output=True, text=True, check=True).stdout

    def commit(self, name, text):
        (self.repo / name).write_text(text)
        self.git("add", name)
        self.git("commit", "-qm", f"change {name}")

    def path(self, ext):
        return self.repo / self.git("rev-parse", "--git-path", f"adversarial-review.{ext}").strip()

    def run_review(self, *args, rc="0"):
        result = subprocess.run([sys.executable, str(SCRIPT), *args], cwd=self.repo, capture_output=True,
                                text=True, env={**self.env, "FAKE_RC": rc})
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout

    def recorded(self):
        return [json.loads(line) for line in self.calls.read_text().splitlines()] if self.calls.exists() else []

    def test_codex_reviews_the_diff_file(self):
        self.commit("app.py", "print('b')\n")
        out = self.run_review("codex", "--focus", "auth only", "diff", "HEAD~1..HEAD")
        self.assertEqual(out, "EXIT=0\n- [P2] codex finding\n")
        self.assertEqual(self.path("exit").read_text(), "EXIT=0\n")
        self.assertIn("print('b')", self.path("diff").read_text())
        [call] = self.recorded()
        args = call["args"]
        self.assertEqual(args[:9], ["exec", "-s", "read-only", "-m", "gpt-6-astra",
                                    "-c", "model_reasoning_effort=high", "-o", str(self.path("md").resolve())])
        self.assertTrue(args[9].startswith(f"The diff under review is in the file {self.path('diff').resolve()}. "
                                           "You are an adversarial code reviewer."))
        self.assertTrue(args[9].endswith("or 'no findings'. auth only"))
        self.assertEqual(call["stdin"], "")
        self.assertIn("trace", self.path("log").read_text())

    def test_claude_reads_the_diff_on_stdin(self):
        self.commit("app.py", "print('b')\n")
        out = self.run_review("claude", "--model", "sonnet", "show", "HEAD", rc="3")
        self.assertEqual(out, "EXIT=3\n- [P2] claude finding\n")
        [call] = self.recorded()
        self.assertEqual(call["args"][:10], ["-p", "--model", "sonnet", "--setting-sources", "", "--tools",
                                             "Read,Grep,Glob", "--strict-mcp-config", "--no-session-persistence",
                                             call["args"][9]])
        self.assertTrue(call["args"][9].startswith("The diff under review is on stdin. You are"))
        self.assertIn("print('b')", call["stdin"])
        self.assertEqual(self.path("log").read_text(), "trace\n")

    def test_git_arguments_after_the_separator_are_kept_verbatim(self):
        self.commit("other.py", "y = 1\n")
        self.commit("app.py", "print('b')\n")
        self.run_review("codex", "--", "diff", "HEAD~2..HEAD", "--", "other.py")
        diff = self.path("diff").read_text()
        self.assertIn("y = 1", diff)
        self.assertNotIn("print('b')", diff)

    def test_uncommitted_includes_untracked_files(self):
        (self.repo / "app.py").write_text("print('c')\n")
        (self.repo / "new file.py").write_text("x = 1\n")
        self.assertEqual(self.run_review("codex", "--uncommitted"), "EXIT=0\n- [P2] codex finding\n")
        diff = self.path("diff").read_text()
        self.assertIn("print('c')", diff)
        self.assertIn("+x = 1", diff)

    def test_failed_or_empty_scope_never_runs_the_reviewer(self):
        self.path("md").write_text("stale findings\n")
        self.assertEqual(self.run_review("codex", "diff", "no-such-ref..HEAD"), "EXIT=diff-failed\n")
        self.assertIn("no-such-ref", self.path("log").read_text())
        self.assertFalse(self.path("md").exists())
        self.assertEqual(self.run_review("claude", "--uncommitted"), "EXIT=empty-diff\n")
        self.assertEqual(self.path("exit").read_text(), "EXIT=empty-diff\n")
        self.assertEqual(self.recorded(), [])

    def test_missing_cli_exits_127(self):
        self.commit("app.py", "print('b')\n")
        git_only = self.repo.parent / "git-only"
        git_only.mkdir()
        (git_only / "git").symlink_to(subprocess.run(["sh", "-c", "command -v git"], capture_output=True,
                                                     text=True, check=True).stdout.strip())
        self.env["PATH"] = str(git_only)
        self.assertEqual(self.run_review("codex", "diff", "HEAD~1..HEAD"), "EXIT=127\n")
        self.assertIn("codex", self.path("log").read_text())

    def test_scope_is_required_once(self):
        for args in (["codex"], ["codex", "--uncommitted", "diff", "HEAD"]):
            result = subprocess.run([sys.executable, str(SCRIPT), *args], cwd=self.repo, capture_output=True,
                                    text=True, env=self.env)
            self.assertEqual(result.returncode, 2, args)


if __name__ == "__main__":
    unittest.main()
