"""Fixture tests for sessions.py: worktree/time selection and both transcript shapes."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest

SCRIPT = Path(__file__).with_name("sessions.py")


class SessionsTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix="bento sessions ")
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.repo = self.root / "work tree"
        self.repo.mkdir()
        subprocess.run(["git", "init", "-q", str(self.repo)], check=True)
        self.top = subprocess.check_output(["git", "-C", str(self.repo), "rev-parse", "--show-toplevel"],
                                           text=True).strip()
        # HOME too: sessions.py also reads every ~/.claude*/projects.
        self.env = {**os.environ, "HOME": str(self.root), "CLAUDE_CONFIG_DIR": str(self.root / "claude"),
                    "CODEX_HOME": str(self.root / "codex")}
        self.claude_dir = self.root / "claude/projects" / "".join(
            c if c.isalnum() else "-" for c in self.top)

    def write(self, path, rows, age=0):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("".join(json.dumps(row) + "\n" for row in rows))
        stamp = time.time() - age
        os.utime(path, (stamp, stamp))
        return path

    def run_script(self, since=None):
        args = [sys.executable, str(SCRIPT), "--repo", str(self.repo)]
        if since is not None:
            args += ["--since", str(since)]
        return subprocess.run(args, env=self.env, capture_output=True, text=True, check=True).stdout

    def test_selects_worktree_sessions_from_both_agents(self):
        cwd = {"cwd": self.top}
        self.write(self.claude_dir / "a.jsonl", [
            {"type": "user", **cwd, "message": {"content": "fix it<system-reminder>noise</system-reminder>"}},
            {"type": "user", "isMeta": True, "message": {"content": "meta"}},
            {"type": "user", "message": {"content": [{"type": "tool_result", "is_error": True, "content": "boom"}]}},
            {"type": "assistant", "message": {"content": [{"type": "text", "text": "assistant-only"}]}},
        ])
        self.write(self.claude_dir.with_name(self.claude_dir.name + "-sub") / "b.jsonl", [
            {"type": "user", "cwd": self.top + "/src", "message": {"content": "nested"}}])
        self.write(self.claude_dir.with_name(self.claude_dir.name + "-other") / "c.jsonl", [
            {"type": "user", "cwd": self.top + "-other", "message": {"content": "sibling worktree"}}])
        self.write(self.root / "codex/sessions/2026/09/23/rollout-x.jsonl", [
            {"type": "session_meta", "payload": {"cwd": self.top}},
            {"type": "response_item", "payload": {"type": "message", "role": "user", "content": [
                {"type": "input_text", "text": "# AGENTS.md instructions for x\n<INSTRUCTIONS>rules</INSTRUCTIONS>"}]}},
            {"type": "response_item", "payload": {"type": "message", "role": "user", "content": [
                {"type": "input_text", "text": "codex ask"}]}},
            {"type": "event_msg", "payload": {"type": "item_completed",
                                              "item": {"status": "failed", "stderr": "exit 1"}}},
        ])
        out = self.run_script(since=0)
        self.assertIn("U: fix it\nERR: boom", out)
        self.assertIn("U: nested", out)
        self.assertIn("U: codex ask\nERR: exit 1", out)
        for absent in ("noise", "meta", "assistant-only", "sibling worktree", "rules"):
            self.assertNotIn(absent, out)
        self.assertEqual(out.count("=== "), 3)
        self.assertNotIn("other directory", out)

    def test_reads_an_operator_turn_sent_as_text_blocks(self):
        # claude -p with stream-json input (Control Room's chat threads) stores the turn as a list of blocks
        self.write(self.claude_dir / "a.jsonl", [
            {"type": "user", "cwd": self.top, "message": {"content": [
                {"type": "text", "text": "why are the buttons missing?"},
                {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": "AAAA"}}]}},
            {"type": "user", "isMeta": True, "message": {"content": [{"type": "text", "text": "meta"}]}},
        ])
        out = self.run_script(since=0)
        self.assertIn("U: why are the buttons missing?", out)
        self.assertNotIn("meta", out)
        self.assertNotIn("AAAA", out)
        self.assertEqual(out.count("=== "), 1)

    def elsewhere(self, name, text, age=0):
        return self.write(self.root / "claude/projects/-elsewhere" / name, [
            {"type": "user", "cwd": str(self.root / "elsewhere"), "message": {"content": text}}], age=age)

    def test_other_directory_session_that_mentions_the_worktree_is_listed(self):
        self.elsewhere("hit.jsonl", f"edit {self.top}/src/x.py")
        self.elsewhere("miss.jsonl", "edit some/other/x.py")
        out = self.run_script(since=0)
        self.assertIn(f"(other directory: {self.root / 'elsewhere'})\nU: edit {self.top}/src/x.py", out)
        self.assertNotIn("some/other", out)

    def test_a_branch_name_alone_does_not_list_another_directorys_session(self):
        # An agent monitoring every thread names every branch; only the worktree path counts.
        git = ["git", "-C", str(self.repo), "-c", "user.name=t", "-c", "user.email=t@t"]
        subprocess.run([*git, "checkout", "-q", "-b", "feature-x"], check=True)
        subprocess.run([*git, "commit", "-q", "--allow-empty", "-m", "x"], check=True)
        self.elsewhere("monitor.jsonl", "threads: feature-x, feature-y, feature-z")
        self.elsewhere("newline.jsonl", f"cd\n{self.top}")
        self.elsewhere("stale.jsonl", f"earlier {self.top}/x.py", age=3600)
        out = self.run_script()
        self.assertNotIn("feature-y", out)
        self.assertIn(f"U: cd\n{self.top}", out)
        self.assertNotIn("earlier", out)

    def test_injected_text_blocks_are_dropped_from_operator_turns(self):
        self.write(self.claude_dir / "blocks.jsonl", [
            {"type": "user", "cwd": self.top, "message": {"content": [
                {"type": "text", "text": "Work on Linear issue IX-1"},
                {"type": "text", "text": "<system-reminder>noise</system-reminder>"}]}},
            {"type": "user", "message": {"content": [
                {"type": "text", "text": "<task-notification>done</task-notification>"}]}},
            {"type": "user", "isMeta": True, "message": {"content": [{"type": "text", "text": "meta"}]}},
        ])
        out = self.run_script(since=0)
        self.assertIn("U: Work on Linear issue IX-1\n\n", out)
        for absent in ("noise", "done", "meta"):
            self.assertNotIn(absent, out)

    def test_sessions_under_every_claude_config_dir_are_read(self):
        for config in ("claude", ".claude", ".claude-rose"):
            self.write(self.root / config / "projects" / self.claude_dir.name / f"{config}.jsonl",
                       [{"type": "user", "cwd": self.top, "message": {"content": f"from {config}/"}}])
        out = self.run_script(since=0)
        for config in ("claude", ".claude", ".claude-rose"):
            self.assertIn(f"U: from {config}/", out)
        self.assertEqual(out.count("=== "), 3)

    def test_a_session_copied_to_another_config_dir_is_read_once(self):
        # Control Room moves a thread to another account by copying its transcript; the original stays.
        for config, text, age in (("claude", "old copy", 60), (".claude-x", "new copy", 0)):
            self.write(self.root / config / "projects" / self.claude_dir.name / "same-id.jsonl",
                       [{"type": "user", "cwd": self.top, "message": {"content": text}}], age=age)
        out = self.run_script(since=0)
        self.assertIn("U: new copy", out)
        self.assertNotIn("old copy", out)
        self.assertEqual(out.count("=== "), 1)

    def test_another_accounts_session_is_listed_by_the_worktree_path(self):
        self.write(self.root / ".claude-x/projects/-elsewhere/path.jsonl", [
            {"type": "user", "cwd": str(self.root / "elsewhere"), "message": {"content": f"foreign edit {self.top}/x.py"}}])
        self.write(self.root / ".claude-x/projects/-copy/copy.jsonl", [
            {"type": "user", "cwd": self.top + '+"copy"/src', "message": {"content": f'sibling {self.top}+"copy"/x'}}])
        out = self.run_script(since=0)
        self.assertIn(f"U: foreign edit {self.top}/x.py", out)
        self.assertNotIn("sibling", out)

    def test_sessions_before_since_are_skipped(self):
        self.write(self.claude_dir / "old.jsonl",
                   [{"type": "user", "cwd": self.top, "message": {"content": "old branch"}}], age=3600)
        self.write(self.claude_dir / "new.jsonl",
                   [{"type": "user", "cwd": self.top, "message": {"content": "this branch"}}])
        out = self.run_script(since=int(time.time()) - 60)
        self.assertIn("this branch", out)
        self.assertNotIn("old branch", out)


if __name__ == "__main__":
    unittest.main()
