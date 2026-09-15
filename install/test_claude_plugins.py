"""Regression tests with real submodules/worktrees and a stateful CLI stand-in."""
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch


spec = importlib.util.spec_from_file_location("installer", Path(__file__).with_name("claude-plugins.py"))
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


class InstallTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix="bento install ")
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name).resolve()
        self.source = self.root / "source"
        self.repo = self.root / "consumer"
        for repo in (self.source, self.repo):
            repo.mkdir()
            self.git(repo, "init", "-q")
            self.git(repo, "config", "user.email", "test@example.com")
            self.git(repo, "config", "user.name", "Test")
        (self.source / "install.sh").touch()
        (self.source / ".claude-plugin").mkdir()
        (self.source / ".claude-plugin/marketplace.json").write_text('{"name":"bento"}')
        self.commit(self.source)
        self.git(self.repo, "-c", "protocol.file.allow=always", "submodule", "add", str(self.source), ".bento")
        self.commit(self.repo)
        self.bento = self.repo / ".bento"
        self.markets = []
        self.plugins = []
        self.calls = []
        self.addCleanup(patch.stopall)
        patch.object(installer.shutil, "which", return_value="claude").start()
        patch.object(installer, "claude", side_effect=self.cli).start()

    def git(self, repo, *args):
        return subprocess.check_output(["git", "-C", str(repo), *args], stderr=subprocess.DEVNULL, text=True)

    def commit(self, repo):
        self.git(repo, "add", ".")
        self.git(repo, "commit", "-qm", "fixture")

    def cli(self, repo, *args, json_output=False):
        self.calls.append(args)
        if args == ("marketplace", "list"):
            return self.markets.copy()
        if args == ("list",):
            return [row.copy() for row in self.plugins]
        if args[:2] == ("marketplace", "add"):
            self.markets.append({"name": "bento", "source": "directory", "path": args[2]})
        elif args[0] == "install":
            cache = self.root / "cache" / args[1]
            cache.mkdir(parents=True, exist_ok=True)
            self.plugins.append({"id": args[1], "scope": "user", "enabled": True, "installPath": str(cache)})
        elif args[0] == "enable":
            for row in self.plugins:
                if row["id"] == args[1]:
                    row["enabled"] = True
        else:
            self.fail(f"Unexpected CLI invocation: {args}")

    def worktree(self):
        work = self.root / "temporary worktree"
        self.git(self.repo, "worktree", "add", "--detach", str(work))
        self.git(work, "-c", "protocol.file.allow=always", "submodule", "update", "--init")
        return work

    def test_bootstrap_and_rerun_skip_mutations(self):
        self.assertEqual(installer.bootstrap(self.bento), self.bento)
        self.assertEqual(len(self.plugins), 2)
        self.calls.clear()
        installer.bootstrap(self.bento)
        self.assertTrue(all(call in (("list",), ("marketplace", "list")) for call in self.calls))

    def test_disabled_plugin_is_enabled_without_reinstall(self):
        installer.bootstrap(self.bento)
        self.plugins[0]["enabled"] = False
        self.calls.clear()
        installer.bootstrap(self.bento)
        self.assertIn(("enable", installer.PLUGINS[0]), self.calls)
        self.assertFalse(any(call[0] == "install" for call in self.calls))

    def test_existing_github_source_is_preserved(self):
        self.markets = [{"name": "bento", "source": "github", "repo": "gnibu/bento"}]
        installer.bootstrap(self.bento)
        self.assertFalse(any(call[:2] == ("marketplace", "add") for call in self.calls))

    def test_other_projects_install_does_not_count(self):
        installer.bootstrap(self.bento)
        self.plugins[0].update(scope="local", projectPath=str(self.root / "other"))
        self.calls.clear()
        installer.bootstrap(self.bento)
        self.assertIn(("install", installer.PLUGINS[0], "--scope", "user"), self.calls)

    def test_worktree_registers_main_checkout(self):
        work = self.worktree()
        self.assertEqual(installer.bootstrap(work / ".bento"), self.bento)
        self.assertEqual(self.markets[0]["path"], str(self.bento))

    def test_worktree_missing_main_submodule_fails_before_cli(self):
        work = self.worktree()
        self.git(self.repo, "submodule", "deinit", "-f", ".bento")
        with self.assertRaisesRegex(RuntimeError, "initialize .bento in the main checkout"):
            installer.bootstrap(work / ".bento")
        self.assertEqual(self.calls, [])

    def test_worktree_different_pin_fails_before_cli(self):
        work = self.worktree()
        self.git(self.bento, "config", "user.email", "test@example.com")
        self.git(self.bento, "config", "user.name", "Test")
        (self.bento / "new-file").touch()
        self.commit(self.bento)
        with self.assertRaisesRegex(RuntimeError, "Align their pins"):
            installer.bootstrap(work / ".bento")
        self.assertEqual(self.calls, [])

    def test_existing_ephemeral_marketplace_is_rejected(self):
        work = self.worktree()
        self.markets = [{"name": "bento", "source": "directory", "path": str(work / ".bento")}]
        with self.assertRaisesRegex(RuntimeError, "temporary worktree"):
            installer.bootstrap(self.bento)

    def test_existing_missing_marketplace_is_rejected(self):
        self.markets = [{"name": "bento", "source": "directory", "path": str(self.root / "gone")}]
        with self.assertRaisesRegex(RuntimeError, "directory is missing"):
            installer.bootstrap(self.bento)

    def test_missing_claude_is_actionable(self):
        with patch.object(installer.shutil, "which", return_value=None):
            with self.assertRaisesRegex(RuntimeError, "CLI on PATH"):
                installer.bootstrap(self.bento)

    def test_nonvendored_install_does_not_call_claude(self):
        self.assertEqual(installer.bootstrap(self.source), self.source)
        self.assertEqual(self.calls, [])


class CliTests(unittest.TestCase):
    def test_timeout_and_failure_and_malformed_json_are_errors(self):
        errors = [subprocess.TimeoutExpired("claude", 300),
                  subprocess.CalledProcessError(1, "claude", "failure", "details")]
        for error in errors:
            with self.subTest(error=error), patch.object(installer.subprocess, "run", side_effect=error):
                with self.assertRaises(RuntimeError):
                    installer.claude(Path.cwd(), "list", json_output=True)
        for output in ("not json", json.dumps({"unexpected": "shape"})):
            with self.subTest(output=output), patch.object(installer.subprocess, "run", return_value=
                    subprocess.CompletedProcess([], 0, output, "")):
                with self.assertRaisesRegex(RuntimeError, "cannot read"):
                    installer.claude(Path.cwd(), "list", json_output=True)


if __name__ == "__main__":
    unittest.main()
