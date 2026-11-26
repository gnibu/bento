import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from agents_block import PRINCIPLES, apply, build_block, recorded_terse

SCRIPT = Path(__file__).with_name("agents_block.py")
CHECK = Path(__file__).resolve().parents[2] / "bento-learn" / "scripts" / "check_entries.py"


def run(*args):
    return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True)


class ApplyTest(unittest.TestCase):
    def test_added_updated_unchanged(self):
        block = build_block(True)
        text, action = apply("# repo\n", block)
        self.assertEqual(action, "added")
        self.assertEqual(text, "# repo\n\n" + block + "\n")
        self.assertEqual(apply(text, block), (text, "unchanged"))
        stale = text.replace(block, "<!-- bento:start -->\nold\n<!-- bento:end -->")
        self.assertEqual(apply(stale, block), (text, "updated"))


class BlockTest(unittest.TestCase):
    def test_inlines_every_section_whole(self):
        block = build_block(True)
        principles = PRINCIPLES.read_text()
        self.assertNotIn(principles.splitlines()[0], block)  # the file's title and intro stay out
        for section in principles.split("\n## ")[1:]:
            heading, _, body = section.partition("\n")
            self.assertIn(f"### {heading}\n\n{body.strip()}", block)

    def test_keeps_the_override_rule_and_records_terse_out_of_sight(self):
        block = build_block(True)
        self.assertIn("This repo's own instructions override them where they overlap.", block)
        self.assertNotIn("no exceptions", block)
        self.assertIn("<!-- bento:terse-reports on -->", block)
        self.assertNotIn("Terse reports:", block)

    def test_block_passes_the_instruction_file_check(self):
        with tempfile.TemporaryDirectory() as tmp:
            for terse in (True, False):
                Path(tmp, "AGENTS.md").write_text(build_block(terse) + "\n")
                result = subprocess.run([sys.executable, str(CHECK), "--all", str(Path(tmp, "AGENTS.md"))],
                                        capture_output=True, text=True)
                self.assertEqual((result.returncode, result.stdout), (0, ""))

    def test_reads_the_answer_an_old_block_recorded(self):
        old = "<!-- bento:start -->\n## bento\n\nTerse reports: off.\n\nx\n<!-- bento:end -->\n"
        self.assertEqual(recorded_terse(old), "off")
        self.assertEqual(recorded_terse(old.replace("off", "on")), "on")

    def test_terse_off_drops_only_report_what_matters(self):
        on, off = build_block(True), build_block(False)
        self.assertIn("### Report what matters", on)
        self.assertNotIn("### Report what matters", off)
        self.assertIn("### Ship through bento-ship", off)
        self.assertEqual((recorded_terse(on), recorded_terse(off), recorded_terse("# repo")), ("on", "off", None))


class CliTest(unittest.TestCase):
    def test_asks_once_then_keeps_the_answer(self):
        with tempfile.TemporaryDirectory() as tmp:
            agents, claude = Path(tmp, "AGENTS.md"), Path(tmp, "CLAUDE.md")
            first = run(str(agents))
            self.assertEqual(first.returncode, 3)  # no answer yet: setup asks
            self.assertFalse(agents.exists())
            self.assertIn("added", run("--terse", "off", str(agents)).stdout)
            # A rerun with no flag reuses the recorded answer, here for a new CLAUDE.md too.
            rerun = run(str(agents), str(claude))
            self.assertEqual(rerun.returncode, 0)
            self.assertIn("unchanged", rerun.stdout)
            self.assertNotIn("Report what matters", claude.read_text())
            self.assertIn("updated", run("--terse", "on", str(agents)).stdout)
            self.assertIn("### Report what matters", agents.read_text())

    def test_old_summary_block_is_replaced_not_duplicated(self):
        with tempfile.TemporaryDirectory() as tmp:
            agents = Path(tmp, "AGENTS.md")
            agents.write_text("# repo\n\n<!-- bento:start -->\n- **Autonomy contract:** old.\n<!-- bento:end -->\n")
            self.assertEqual(run(str(agents)).returncode, 3)  # never asked before
            self.assertIn("updated", run("--terse", "on", str(agents)).stdout)
            self.assertEqual(agents.read_text().count("<!-- bento:start -->"), 1)


if __name__ == "__main__":
    unittest.main()
