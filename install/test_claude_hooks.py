"""Prove project and personal hook activation survives creating another worktree."""
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest


spec = importlib.util.spec_from_file_location("claude_hooks", Path(__file__).with_name("bento-claude-hooks.py"))
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


class ClaudeHooksTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix="bento claude hooks ")
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name).resolve()
        self.repo = self.root / "consumer"
        self.repo.mkdir()
        self.config = self.root / "claude-config"
        self.git(self.repo, "init", "-q")
        self.git(self.repo, "config", "user.email", "test@example.com")
        self.git(self.repo, "config", "user.name", "Test")
        scripts = self.repo / ".bento/plugins/bento-forge/scripts"
        scripts.mkdir(parents=True)
        (scripts / "session-start.sh").write_text('cat > "$BENTO_TEST_MARKER"\n')

    def git(self, repo, *args):
        return subprocess.check_output(["git", "-C", str(repo), *args], text=True, stderr=subprocess.DEVNULL)

    def install(self, repo=None, **kwargs):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            installer.install(repo or self.repo, self.config, **kwargs)
        return output.getvalue()

    def worktree(self):
        self.git(self.repo, "add", ".")
        self.git(self.repo, "commit", "-qm", "project setup")
        work = self.root / "new worktree"
        self.git(self.repo, "worktree", "add", "--detach", str(work))
        return work

    def fire(self, path, cwd, expected=True):
        hooks = json.loads(path.read_text())["hooks"]
        self.assertNotIn("Stop", hooks)
        marker = self.root / "marker"
        command = hooks["SessionStart"][-1]["hooks"][0]["command"]
        subprocess.run(["bash", "-c", command], cwd=cwd, input="SessionStart", text=True,
                       env={**os.environ, "BENTO_TEST_MARKER": str(marker)}, check=True)
        self.assertEqual(marker.exists(), expected)
        if expected:
            self.assertEqual(marker.read_text(), "SessionStart")
            marker.unlink()

    def test_committed_settings_are_inherited_by_new_worktree(self):
        self.install()
        work = self.worktree()
        self.assertFalse((work / ".claude/settings.local.json").exists())
        self.fire(work / ".claude/settings.json", work)
        self.assertIn("no Claude hook changes", self.install(work))

    def test_personal_hooks_cover_same_repo_worktrees_only(self):
        self.install(scope="personal")
        work = self.worktree()
        nested = work / "src/nested"
        nested.mkdir(parents=True)
        path = self.config / "settings.json"
        self.fire(path, nested)
        self.assertIn("no Claude hook changes", self.install(work, scope="personal"))
        other = self.root / "other"
        other.mkdir()
        self.git(other, "init", "-q")
        # Even another Bento consumer must not activate this repo's personal hooks.
        self.fire(path, other, expected=False)

    def test_preserves_existing_settings_and_hooks_through_purge(self):
        self.config.mkdir()
        path = self.config / "settings.json"
        original = {"permissions": {"allow": ["Read"]}, "hooks": {
            "Stop": [{"hooks": [{"type": "command", "command": "echo notify"}]}]}}
        path.write_text(json.dumps(original))
        self.install(scope="personal")
        self.install(scope="personal", purge=True)
        self.assertEqual(json.loads(path.read_text()), original)

    def test_rerun_removes_retired_stop_hook(self):
        path = self.repo / ".claude/settings.json"
        path.parent.mkdir()
        legacy = ('bento_repo="$(git rev-parse --show-toplevel 2>/dev/null)" || exit 0; '
                  'bento_hook="$bento_repo/.bento/plugins/bento-forge/scripts/session-stop.sh"; '
                  '[ ! -f "$bento_hook" ] || BENTO_IMPROVE_AUTO_PR=1 bash "$bento_hook"')
        keep = {"type": "command", "command": "echo notify"}
        path.write_text(json.dumps({"hooks": {"Stop": [
            {"hooks": [keep, {"type": "command", "command": legacy, "timeout": 5}]}]}}))
        self.install()
        hooks = json.loads(path.read_text())["hooks"]
        self.assertEqual(hooks["Stop"], [{"hooks": [keep]}])
        self.assertEqual(len(hooks["SessionStart"]), 1)


if __name__ == "__main__":
    unittest.main()
