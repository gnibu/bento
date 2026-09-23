"""Fixture tests; set BENTO_TEST_CODEX=1 to verify real prompt-input discovery."""
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import tomllib
import unittest


SOURCE = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("codex_install", SOURCE / "install/bento-codex.py")
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


class CodexTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix="bento codex ")
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name).resolve()
        self.repo = self.root / "consumer"
        self.repo.mkdir()
        subprocess.run(["git", "init", "-q", str(self.repo)], check=True)
        self.home = self.root / "codex-home"
        self.home.mkdir()
        shutil.copytree(SOURCE / "plugins", self.repo / ".bento/plugins")
        self.skills = self.repo / ".codex/skills"

    def install(self, **kwargs):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            installer.install(self.repo, self.home, **kwargs)
        return output.getvalue()

    def test_install_repeat_and_relative_links(self):
        output = self.install()
        targets = list((self.repo / installer.CORE).iterdir())
        self.assertEqual(len(list(self.skills.iterdir())), len(targets) + 1)
        for source in targets:
            link = self.skills / source.name
            self.assertTrue(link.is_symlink())
            self.assertFalse(os.path.isabs(os.readlink(link)))
            self.assertEqual(link.resolve(), source)
        hooks = self.home / "hooks.json"
        before = hooks.read_bytes()
        self.assertIn("configured", output)
        self.assertIn("fresh Codex session", output)
        self.assertIn("no changes needed", self.install())
        self.assertEqual(hooks.read_bytes(), before)

    def test_collisions_do_not_partially_install(self):
        for kind in ("file", "directory", "link", "broken-link"):
            with self.subTest(kind=kind):
                self.skills.mkdir(parents=True, exist_ok=True)
                dest = self.skills / "ship"
                if kind == "file":
                    dest.write_text("keep")
                elif kind == "directory":
                    dest.mkdir()
                else:
                    dest.symlink_to(self.root if kind == "link" else self.root / "missing")
                with self.assertRaisesRegex(ValueError, "collision"):
                    self.install()
                self.assertEqual(list(self.skills.iterdir()), [dest])
                self.assertFalse((self.home / "hooks.json").exists())
                if kind == "directory":
                    dest.rmdir()
                else:
                    dest.unlink()

    def test_hook_and_unrelated_link_preservation_and_purge(self):
        self.skills.mkdir(parents=True)
        unrelated = self.skills / "personal"
        unrelated.symlink_to(self.root / "missing-personal-skill")
        handler = {"type": "command", "command": "echo unrelated"}
        original = {"description": "keep metadata", "hooks": {
            "SessionStart": [{"matcher": "*", "hooks": [handler]}],
            "PreToolUse": [{"hooks": [handler]}]}}
        hook_path = self.home / "hooks.json"
        hook_path.write_text(json.dumps(original))
        self.install()
        # Preserve an unrelated handler added to the same group as our own hook.
        mixed = json.loads(hook_path.read_text())
        mixed["hooks"]["SessionStart"][-1]["hooks"].append(handler)
        hook_path.write_text(json.dumps(mixed))
        self.install(purge=True)
        result = json.loads(hook_path.read_text())
        self.assertEqual(result["description"], original["description"])
        self.assertEqual(result["hooks"]["PreToolUse"], original["hooks"]["PreToolUse"])
        self.assertEqual(result["hooks"]["SessionStart"][0], original["hooks"]["SessionStart"][0])
        self.assertEqual(result["hooks"]["SessionStart"][1]["hooks"], [handler])
        self.assertEqual(list(self.skills.iterdir()), [unrelated])
        self.assertIn("no changes needed", self.install(purge=True))

    def test_purge_after_submodule_removal_preserves_replaced_skill(self):
        self.install()
        replaced = self.skills / "ship"
        replaced.unlink()
        replaced.mkdir()
        shutil.rmtree(self.repo / ".bento")
        self.install(purge=True)
        self.assertEqual(list(self.skills.iterdir()), [replaced])

    def test_team_hooks_preserve_toml_and_purge(self):
        config = self.repo / ".codex/config.toml"
        config.parent.mkdir()
        original = '# user comment\nmodel = "example"\n[features]\nhooks = true\n[[hooks.Stop]]\n[[hooks.Stop.hooks]]\ntype = "command"\ncommand = "echo keep"\n'
        config.write_text(original)
        self.install(hooks="team")
        hooks = tomllib.loads(config.read_text())["hooks"]
        self.assertEqual((len(hooks["Stop"]), len(hooks["SessionStart"])), (1, 1))
        self.assertTrue(config.read_text().startswith(original))
        self.assertFalse((self.home / "hooks.json").exists())
        self.assertIn("no changes needed", self.install(hooks="team"))
        self.install(hooks="team", purge=True)
        self.assertEqual(config.read_text(), original)

    def test_invalid_hooks_refuse_before_link_creation(self):
        (self.home / "hooks.json").write_text('{"hooks": []}')
        with self.assertRaises(ValueError):
            self.install()
        self.assertFalse(self.skills.exists())

    def test_custom_entries_inside_team_block_are_never_overwritten(self):
        self.install(hooks="team")
        config = self.repo / ".codex/config.toml"
        custom = config.read_text().replace(installer.END,
            '[[hooks.Stop.hooks]]\ntype = "command"\ncommand = "echo keep"\n' + installer.END)
        config.write_text(custom)
        for purge in (False, True):
            with self.assertRaisesRegex(ValueError, "block was edited"):
                self.install(hooks="team", purge=purge)
            self.assertEqual(config.read_text(), custom)
            self.assertTrue((self.skills / "ship").is_symlink())

    def test_edited_bento_handler_inside_team_block_is_never_overwritten(self):
        self.install(hooks="team")
        config = self.repo / ".codex/config.toml"
        original = config.read_text()
        for edited in (original.replace("timeout = 5", "timeout = 60"),
                       original.replace('bash \\"$bento_hook\\"',
                                        'bash \\"$bento_hook\\"; echo extra')):
            with self.subTest(edited=edited):
                self.assertNotEqual(edited, original)
                config.write_text(edited)
                for purge in (False, True):
                    with self.assertRaisesRegex(ValueError, "block was edited"):
                        self.install(hooks="team", purge=purge)
                    self.assertEqual(config.read_text(), edited)

    def test_legacy_team_block_is_rewritten_without_stop(self):
        config = self.repo / ".codex/config.toml"
        config.parent.mkdir()
        for auto_pr in (False, True):
            with self.subTest(auto_pr=auto_pr):
                lines = [installer.START]
                for event, script in (("SessionStart", "session-start.sh"), ("Stop", "session-stop.sh")):
                    command = installer.hook_command().replace("session-start.sh", script)
                    if event == "Stop" and auto_pr:
                        command = command.replace('bash "$bento_hook"',
                                                  'BENTO_IMPROVE_AUTO_PR=1 bash "$bento_hook"')
                    lines += [f"[[hooks.{event}]]", f"[[hooks.{event}.hooks]]", 'type = "command"',
                              "command = " + json.dumps(command), "timeout = 5", ""]
                config.write_text("\n".join(lines) + installer.END + "\n")
                self.install(hooks="team")
                hooks = tomllib.loads(config.read_text())["hooks"]
                self.assertEqual(list(hooks), ["SessionStart"])

    def test_legacy_duplicate_hooks_are_reconciled(self):
        unrelated = {"type": "command", "command": "echo keep"}
        legacy = {
            "SessionStart": (
                'repo="$(git rev-parse --show-toplevel 2>/dev/null)"; '
                'bash "$repo/.bento/plugins/bento-forge/scripts/session-start.sh"'
            ),
            "Stop": (
                'repo="$(git rev-parse --show-toplevel 2>/dev/null)"; '
                'bash "$repo/.bento/plugins/bento-forge/scripts/session-stop.sh"'
            ),
        }
        hooks = {}
        for event in ("SessionStart", "Stop"):
            hooks[event] = [{"hooks": [
                unrelated,
                {"type": "command", "command": legacy[event], "timeout": 5},
                {"type": "command", "command": installer.hook_command(), "timeout": 5},
            ]}]
        hook_path = self.home / "hooks.json"
        hook_path.write_text(json.dumps({"hooks": hooks}))

        self.install()

        result = json.loads(hook_path.read_text())["hooks"]
        for event in ("SessionStart", "Stop"):
            handlers = [handler for group in result[event] for handler in group["hooks"]]
            self.assertIn(unrelated, handlers)
            bento = [handler for handler in handlers
                     if ".bento/plugins/bento-forge/scripts/" in handler.get("command", "")]
            expected = {"type": "command", "command": installer.hook_command(), "timeout": 5}
            self.assertEqual(bento, [expected] if event == "SessionStart" else [])

    def test_hook_commands_run_real_paths_from_nested_directory_and_noop_elsewhere(self):
        self.install()
        nested = self.repo / "src/nested"
        nested.mkdir(parents=True)
        marker = self.root / "fired"
        env = {**os.environ, "BENTO_TEST_MARKER": str(marker)}
        (self.repo / ".bento/plugins/bento-forge/scripts/session-start.sh").write_text(
            '#!/bin/bash\ncat > "$BENTO_TEST_MARKER"\n')
        subprocess.run(["bash", "-c", installer.hook_command()], cwd=nested,
                       input="SessionStart", text=True, env=env, check=True)
        self.assertEqual(marker.read_text(), "SessionStart")
        marker.unlink()
        subprocess.run(["bash", "-c", installer.hook_command()], cwd=self.root,
                       input="SessionStart", text=True, env=env, check=True)
        self.assertFalse(marker.exists())

    @unittest.skipUnless(os.environ.get("BENTO_TEST_CODEX") == "1" and shutil.which("codex"),
                         "set BENTO_TEST_CODEX=1 with codex installed")
    def test_real_codex_prompt_input_discovery_and_purge(self):
        self.install()
        env = {**os.environ, "CODEX_HOME": str(self.home)}
        def prompt():
            result = subprocess.run(["codex", "debug", "prompt-input", "List Bento skills"],
                                    cwd=self.repo, env=env, text=True, capture_output=True,
                                    check=True, timeout=60)
            return json.dumps(json.loads(result.stdout))
        before = prompt()
        for path in (self.repo / installer.CORE).iterdir():
            self.assertIn(f"bento-core:{path.name}", before)
        self.assertIn("bento-forge:bento-improve", before)
        self.install(purge=True)
        after = prompt()
        self.assertNotIn("bento-core:checkpoint", after)
        self.assertNotIn("bento-forge:bento-improve", after)


if __name__ == "__main__":
    unittest.main()
