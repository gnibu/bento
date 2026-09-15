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
            "Stop": [{"matcher": "*", "hooks": [handler]}],
            "PreToolUse": [{"hooks": [handler]}]}}
        hook_path = self.home / "hooks.json"
        hook_path.write_text(json.dumps(original))
        self.install()
        # Preserve an unrelated handler added to the same group as our own hook.
        mixed = json.loads(hook_path.read_text())
        mixed["hooks"]["Stop"][-1]["hooks"].append(handler)
        hook_path.write_text(json.dumps(mixed))
        self.install(purge=True)
        result = json.loads(hook_path.read_text())
        self.assertEqual(result["description"], original["description"])
        self.assertEqual(result["hooks"]["PreToolUse"], original["hooks"]["PreToolUse"])
        self.assertEqual(result["hooks"]["Stop"][0], original["hooks"]["Stop"][0])
        self.assertEqual(result["hooks"]["Stop"][1]["hooks"], [handler])
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
        self.assertEqual(len(tomllib.loads(config.read_text())["hooks"]["Stop"]), 2)
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

    def test_auto_pr_updates_only_stop_hook(self):
        self.install()
        self.install(auto_pr=True)
        data = json.loads((self.home / "hooks.json").read_text())["hooks"]
        self.assertEqual(len(data["Stop"]), 1)
        self.assertIn("BENTO_IMPROVE_AUTO_PR=1", data["Stop"][0]["hooks"][0]["command"])
        self.assertNotIn("BENTO_IMPROVE_AUTO_PR", data["SessionStart"][0]["hooks"][0]["command"])

    def test_hook_commands_run_real_paths_from_nested_directory_and_noop_elsewhere(self):
        self.install()
        nested = self.repo / "src/nested"
        nested.mkdir(parents=True)
        marker = self.root / "fired"
        env = {**os.environ, "BENTO_TEST_MARKER": str(marker)}
        for event, script in (("SessionStart", "session-start.sh"), ("Stop", "session-stop.sh")):
            (self.repo / ".bento/plugins/bento-forge/scripts" / script).write_text(
                '#!/bin/bash\ncat > "$BENTO_TEST_MARKER"\n')
            subprocess.run(["bash", "-c", installer.hook_command(event)], cwd=nested,
                           input=event, text=True, env=env, check=True)
            self.assertEqual(marker.read_text(), event)
            marker.unlink()
            subprocess.run(["bash", "-c", installer.hook_command(event)], cwd=self.root,
                           input=event, text=True, env=env, check=True)
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
