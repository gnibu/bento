"""Tests for check_entries.py: which new instruction-file entries are rejected."""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from check_entries import check, entries, menu_gaps, misplaced

SCRIPT = Path(__file__).with_name("check_entries.py")
LONG = "Run the full suite with the database container up, then the browser tests, " \
       "then the linter, and only then the type checker, because"


class CheckEntriesTests(unittest.TestCase):
    def test_splits_bullets_paragraphs_and_code_blocks(self):
        text = "# Title\n\n- one\n  wrapped\n- two\n\npara\ngraph\n<!-- note -->\n```\nmake\n- x\n```\n"
        self.assertEqual(entries(text), ["- one wrapped", "- two", "para graph", "``` make - x ```"])

    def test_short_fact_passes_without_pointer(self):
        self.assertEqual(check("", "- Base branch: `main`.\n"), [])

    def test_two_lines_need_a_pointer(self):
        bare = f"- **Testing:** {LONG}.\n"
        self.assertEqual(len(check("", bare)), 1)
        self.assertEqual(check("", f"- **Testing:** {LONG[:60]}. See docs/procedures/run-tests.md.\n"), [])
        self.assertEqual(check("", f"- **Testing:** {LONG[:60]}. See [guide](guide).\n"), [])

    def test_over_two_lines_rejected_even_with_pointer(self):
        rejected = check("", f"- **Testing:** {LONG} {LONG}. See docs/procedures/run-tests.md.\n")
        self.assertIn("over two lines", rejected[0][1])

    def test_procedure_code_block_rejected(self):
        block = "```sh\n" + "\n".join(f"step-{i} --with-a-flag --and-another" for i in range(6)) + "\n```\n"
        self.assertEqual(len(check("", block)), 1)

    def test_table_rows_are_separate_entries(self):
        rows = "".join(f"| Task {i} | docs/procedures/task-{i}.md |\n" for i in range(8))
        table = "| When | Read |\n|---|---|\n" + rows
        self.assertEqual(len(entries(table)), 10)
        self.assertEqual(check(table, table + "| Migrating | docs/procedures/migrate.md |\n"), [])
        self.assertEqual(len(check(table, table + f"| {LONG} {LONG} |\n")), 1)

    def test_only_new_or_changed_entries_are_checked(self):
        old = f"- {LONG} {LONG}\n"
        self.assertEqual(check(old, old + "- Base branch: `main`.\n"), [])
        self.assertEqual(len(check(old, old.replace("Run", "Start"))), 1)

    def test_menu_names_every_doc_by_file_or_folder(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name in ("docs/procedures/run-tests.md", "docs/briefs/a.md", "docs/briefs/b.md",
                         "docs/DEPLOY.md"):
                Path(root, name).parent.mkdir(parents=True, exist_ok=True)
                Path(root, name).write_text("x")
            menu = "## Docs\n\n- Running tests → docs/procedures/run-tests.md\n- Briefs → docs/briefs/\n"
            self.assertEqual(menu_gaps(root, menu), ["docs/DEPLOY.md"])
            self.assertEqual(menu_gaps(root, "## Docs\n\nSee docs/ for everything."), [
                "docs/DEPLOY.md", "docs/briefs/a.md", "docs/briefs/b.md", "docs/procedures/run-tests.md"])
            # A file link doesn't name its folder, and a proposed doc must be listed too.
            self.assertEqual(menu_gaps(root, menu + "- Deploying → docs/DEPLOY.md\n",
                                       ["docs/procedures/release.md"]), ["docs/procedures/release.md"])

    def test_only_the_docs_section_counts(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "docs").mkdir()
            Path(tmp, "docs", "DEPLOY.md").write_text("x")
            menu = "## Docs\n\n- Deploying → docs/DEPLOY.md.\n\n## Other\n"
            self.assertEqual(menu_gaps(Path(tmp), menu), [])
            self.assertEqual(menu_gaps(Path(tmp), "## Docs\n\n## Other\n- docs/DEPLOY.md\n"),
                             ["docs/DEPLOY.md"])

    def test_no_docs_dir_still_checks_proposed_docs(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(menu_gaps(Path(tmp), "- x\n"), [])
            self.assertEqual(menu_gaps(Path(tmp), "- x\n", ["docs/procedures/run-tests.md"]),
                             ["docs/procedures/run-tests.md"])

    def test_without_a_menu_only_new_docs_count_and_ignored_docs_never(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            subprocess.run(["git", "init", "-q", tmp], check=True)
            for name in ("docs/DEPLOY.md", "docs/résumé.md", "docs/.venv/pkg/LICENSE.md"):
                Path(root, name).parent.mkdir(parents=True, exist_ok=True)
                Path(root, name).write_text("x")
            Path(root, ".gitignore").write_text(".venv/\n")
            table = "| When | Read |\n|---|---|\n| Deploying | docs/procedures/deploy.md |\n"
            self.assertEqual(menu_gaps(root, table), [])
            self.assertEqual(menu_gaps(root, table, ["docs/procedures/deploy.md"]), [])
            self.assertEqual(menu_gaps(root, table, ["docs/procedures/release.md"]),
                             ["docs/procedures/release.md"])
            # With a menu, every doc on disk counts, but never an ignored one.
            self.assertEqual(menu_gaps(root, "## Docs\n\n- x\n"), ["docs/DEPLOY.md", "docs/résumé.md"])

    def test_new_entry_about_one_subfolder_is_misplaced(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for folder in ("control-room/e2e", "app", "docs/procedures", ".conductor",
                           "plugins/bento/evals/case", "plugins/bento/skills/x"):
                Path(root, folder).mkdir(parents=True)
            Path(root, "CHANGELOG.md").write_text("x")
            Path(root, "LICENSE").write_text("x")
            Path(root, "plugins/bento/evals/AGENTS.md").write_text("x")
            old = "- e2e: `node control-room/e2e/drive.js`; fakes in `control-room/test/fakes/`.\n"
            tip = "- **Tests clobber threads:** run `CR_HOME=$(mktemp -d) npm test` in control-room/.\n"
            self.assertEqual(misplaced(root, old, old + tip), [(tip.strip(), "control-room")])
            # The nearest AGENTS.md over every path, else the deepest folder they share.
            nested = "- Cases: plugins/bento/evals/case/setup.sh runs first.\n"
            self.assertEqual(misplaced(root, old, old + nested), [(nested.strip(), "plugins/bento/evals")])
            deep = "- See plugins/bento/skills/x/a.py and plugins/bento/skills/x/b.py.\n"
            self.assertEqual(misplaced(root, old, old + deep), [(deep.strip(), "plugins/bento/skills/x")])
            # A correction of an existing line, a cross-cutting entry, docs/ and home paths pass.
            self.assertEqual(misplaced(root, old, old.replace("test/fakes", "e2e/fakes")), [])
            for entry in ("- See control-room/README.md and app/main.py.\n",
                          "- Update CHANGELOG.md when adding a case under plugins/bento/evals/.\n",
                          "- Run .conductor/setup.sh and control-room/e2e/drive.js.\n",
                          "- Before running tests → docs/procedures/run-tests.md\n",
                          "- Logs: ~/.nightshift/control-room/chats/ and $HOME/x/y.\n",
                          "- See https://example.com/control-room/x.\n",
                          "- Missing folder: nowhere/x.js.\n",
                          "- Check plugins/../CHANGELOG.md.\n",
                          "- Follow LICENSE when copying plugins/bento/evals/ fixtures.\n"):
                self.assertEqual(misplaced(root, old, old + entry), [], entry)
            # A glob keeps its folder; a link counts by its target, not its label.
            glob = "- Run the tests in plugins/bento/skills/*/scripts/.\n"
            self.assertEqual(misplaced(root, old, old + glob), [(glob.strip(), "plugins/bento/skills")])
            link = "- See [AGENTS.md](plugins/bento/evals/AGENTS.md).\n"
            self.assertEqual(misplaced(root, old, old + link), [(link.strip(), "plugins/bento/evals")])
            # One corrected line exempts only the new line most like it, wherever it sits.
            fixed = old.replace("test/fakes", "e2e/fakes")
            twin = "- e2e: `node control-room/e2e/drive.js`; fakes also in `control-room/e2e/x/`.\n"
            self.assertEqual(misplaced(root, old, twin + fixed), [(twin.strip(), "control-room/e2e")])

    def test_cli_exit_codes_and_missing_current_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            proposed = Path(tmp, "proposed.md")
            missing = Path(tmp, "pkg", "AGENTS.md")
            proposed.write_text("- Base branch: `main`.\n")
            run = lambda: subprocess.run([sys.executable, SCRIPT, missing, proposed],
                                         capture_output=True, text=True)
            self.assertEqual(run().returncode, 0)
            proposed.write_text(f"- {LONG} {LONG}\n")
            result = run()
            self.assertEqual(result.returncode, 1)
            self.assertIn("over two lines", result.stdout)
            Path(tmp, "docs").mkdir()
            Path(tmp, "docs", "DEPLOY.md").write_text("x")
            agents = Path(tmp, "AGENTS.md")
            proposed.write_text("- Base branch: `main`.\n\n## Docs\n\n- Read the code.\n")
            result = subprocess.run([sys.executable, SCRIPT, agents, proposed], capture_output=True, text=True)
            self.assertEqual(result.returncode, 1)
            self.assertIn("menu misses docs/DEPLOY.md", result.stdout)
            Path(tmp, "pkg").mkdir()
            proposed.write_text("- In pkg/, run `make` before pkg/test.sh.\n")
            result = subprocess.run([sys.executable, SCRIPT, agents, proposed], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0)  # a warning never fails
            self.assertIn("warning:", result.stdout)
            self.assertIn("pkg/AGENTS.md (new: with a CLAUDE.md holding @AGENTS.md)", result.stdout)
            # Only the repository's root AGENTS.md warns: a nested one is already the cheap home.
            subprocess.run(["git", "init", "-q", tmp], check=True)
            Path(tmp, "pkg", "sub").mkdir()
            proposed.write_text("- In sub/, run `make` before sub/test.sh.\n")
            result = subprocess.run([sys.executable, SCRIPT, Path(tmp, "pkg", "AGENTS.md"), proposed],
                                    capture_output=True, text=True)
            self.assertNotIn("warning:", result.stdout)


if __name__ == "__main__":
    unittest.main()
