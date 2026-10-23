"""Repo-level checks for bento's own dogfood setup (see AGENTS.md). Run: python3 -m unittest discover tests"""
import runpy
import subprocess
import tempfile
import tomllib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
AGENTS_BLOCK = runpy.run_path(str(ROOT / "plugins/bento/skills/bento-setup/scripts/agents_block.py"))


class DogfoodTest(unittest.TestCase):
    def test_setup_links_skills_idempotently(self):
        setup = tomllib.loads((ROOT / ".conductor/settings.toml").read_text())["scripts"]["setup"]
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "plugins/bento").mkdir(parents=True)
            (Path(tmp) / "plugins/bento/skills").symlink_to(ROOT / "plugins/bento/skills")
            for _ in range(2):
                subprocess.run(setup, shell=True, cwd=tmp, check=True)
            for link in (".agents/skills", ".claude/skills"):
                self.assertTrue((Path(tmp) / link / "bento-ship/SKILL.md").is_file(), link)

    def test_setup_refuses_a_real_skills_directory(self):
        setup = tomllib.loads((ROOT / ".conductor/settings.toml").read_text())["scripts"]["setup"]
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / ".agents/skills").mkdir(parents=True)
            run = subprocess.run(setup, shell=True, cwd=tmp, capture_output=True)
            self.assertNotEqual(run.returncode, 0)
            self.assertFalse((Path(tmp) / ".agents/skills/skills").exists())

    def test_links_are_gitignored(self):
        out = subprocess.run(["git", "check-ignore", ".agents/skills", ".claude/skills"],
                             cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(out.stdout.split(), [".agents/skills", ".claude/skills"])

    def test_agents_md_principles_block_is_current(self):
        text = (ROOT / "AGENTS.md").read_text()
        terse = AGENTS_BLOCK["recorded_terse"](text)
        self.assertIsNotNone(terse, "AGENTS.md block records no --terse answer")
        self.assertEqual(AGENTS_BLOCK["apply"](text, AGENTS_BLOCK["build_block"](terse))[1], "unchanged",
                         "rerun plugins/bento/skills/bento-setup/scripts/agents_block.py AGENTS.md")


if __name__ == "__main__":
    unittest.main()
