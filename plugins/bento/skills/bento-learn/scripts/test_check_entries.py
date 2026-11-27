"""Tests for check_entries.py: which new instruction-file entries are rejected."""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from check_entries import BUDGET, check, entries, menu_gaps, misplaced, over_budget

SCRIPT = Path(__file__).with_name("check_entries.py")
AGENTS_BLOCK = Path(__file__).resolve().parents[2] / "bento-setup" / "scripts" / "agents_block.py"
BLOCK = "<!-- bento:start -->\n- **Commit, push or PR request → run `bento-ship`**, never `git commit`.\n<!-- bento:end -->\n"


def bento_block(terse):
    """The block bento-setup generates today."""
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run([sys.executable, AGENTS_BLOCK, "--terse", terse, f"{tmp}/AGENTS.md"],
                       check=True, capture_output=True)
        return Path(tmp, "AGENTS.md").read_text()
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

    def test_entry_restating_a_principle_is_rejected(self):
        rejected = check("", BLOCK + "- Asked to commit or open a PR: run bento-ship.\n")
        self.assertEqual(len(rejected), 1)
        self.assertIn("may restate the bento block's", rejected[0][1])
        # The block itself, a repo fact that shares a word or two, and an old line all pass.
        for entry in ("- Tests: `npm test` before a PR.\n", "- Deploy: `make deploy`; never on Fridays.\n"):
            self.assertEqual(check("", BLOCK + entry), [], entry)
        old = BLOCK + "- Asked to commit or open a PR: run bento-ship.\n"
        self.assertEqual(check(old, old), [])
        # No block in the file or the one it sits under: nothing to restate.
        self.assertEqual(check("", "- Asked to commit or open a PR: run bento-ship.\n"), [])

    def test_restatement_is_judged_against_the_block_the_repo_loads(self):
        on, off = bento_block("on"), bento_block("off")
        for entry in ("- **Shipping:** run `/bento-ship` for every commit, push or PR.\n",
                      "- Never edit the installed bento-* skills; put changes in .agents/bento/ overlays.\n"):
            self.assertEqual(len(check(on, on + entry)), 1, entry)
        # A repo rule that only shares words with a principle stays.
        self.assertEqual(check(on, on + "- Never push to production.\n"), [])
        # Terse reports off: the block has no "Report what matters", so the repo's copy is the only one.
        self.assertEqual(check(off, off + "- Never shorten failing tests or security warnings.\n"), [])
        self.assertEqual(len(check(on, on + "- Never shorten failing tests or security warnings.\n")), 1)
        # A verbatim copy of a block line, outside the block, is new and a restatement.
        copy = next(line for line in on.splitlines() if "Irreversible writes" in line)
        self.assertEqual(len(check(on, on + copy + "\n")), 1)
        # A nested file is judged against the root block it loads with.
        self.assertEqual(len(check("", "- Asked to commit or open a PR: run bento-ship.\n", on)), 1)

    def test_restatement_only_warns(self):
        on = bento_block("on")
        # A stricter rule shares a principle's words too ("never" where it says "confirm first").
        with tempfile.TemporaryDirectory() as tmp:
            current, proposed = Path(tmp, "AGENTS.md"), Path(tmp, "proposed.md")
            current.write_text(on)
            proposed.write_text(on + "- Never force-push, deploy, or delete data.\n")
            result = subprocess.run([sys.executable, SCRIPT, current, proposed], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout)
            self.assertIn("AGENTS.md: warning: - Never force-push", result.stdout)
            self.assertIn("may restate the bento block's \"- **Irreversible writes", result.stdout)

    def test_root_file_over_budget_warns_only_when_it_grows(self):
        lines = "".join(f"- Fact {i}.\n" for i in range(BUDGET))
        self.assertIsNone(over_budget("", lines))
        self.assertEqual(over_budget(lines, lines + "- One more.\n"), BUDGET + 1)
        self.assertIsNone(over_budget(lines + "- One more.\n", lines + "- Another.\n"))  # same size
        self.assertIsNone(over_budget("", BLOCK * 30 + lines))  # the bento block doesn't count

    def test_cli_all_checks_every_entry_and_diff_only_the_branch(self):
        with tempfile.TemporaryDirectory() as tmp:
            git = lambda *a: subprocess.run(["git", "-C", tmp, *a], check=True, capture_output=True)
            git("init", "-q", "-b", "main")
            git("config", "user.email", "a@b.c")
            git("config", "user.name", "a")
            agents = Path(tmp, "AGENTS.md")
            agents.write_text(bento_block("on") + f"- {LONG} {LONG}\n")
            Path(tmp, "old").mkdir()
            Path(tmp, "old", "AGENTS.md").write_text(f"- {LONG} {LONG}\n")
            git("add", "-A")
            git("commit", "-q", "-m", "init")
            git("switch", "-q", "-c", "feature")
            run = lambda *a: subprocess.run([sys.executable, SCRIPT, *a], capture_output=True,
                                            text=True, cwd=tmp)
            self.assertEqual(run("--all", str(agents)).returncode, 1)  # the old entry counts too
            self.assertEqual(run("--all", str(Path(tmp, "nowhere", "AGENTS.md"))).returncode, 0)
            self.assertEqual(run("--diff", "main").returncode, 0)  # nothing changed
            # A new CLAUDE.md alias, a moved file and a link out of the checkout add no entry.
            Path(tmp, "CLAUDE.md").symlink_to("AGENTS.md")
            git("mv", "old", "moved")
            outside = Path(tmp, "..", Path(tmp).name + "-outside.md").resolve()
            outside.write_text(f"- {LONG} {LONG}\n")
            self.addCleanup(outside.unlink)
            Path(tmp, "linked").mkdir()
            Path(tmp, "linked", "CLAUDE.md").symlink_to(outside)
            git("add", "-A")
            git("commit", "-q", "-m", "alias, move, link")
            result = run("--diff", "main")
            self.assertEqual((result.returncode, result.stdout), (0, ""))
            # A feature agent's direct edits: committed in a nested file, uncommitted at the root.
            Path(tmp, "pkg").mkdir()
            Path(tmp, "pkg", "AGENTS.md").write_text("- Asked to commit or open a PR: run bento-ship.\n")
            git("add", "-A")
            git("commit", "-q", "-m", "feature agent edits")
            agents.write_text(agents.read_text() + f"- **Testing:** {LONG}.\n")
            result = run("--diff", "main")
            self.assertEqual(result.returncode, 1)
            self.assertEqual(result.stdout.count("AGENTS.md:"), 2, result.stdout)  # symlink once
            self.assertIn("pkg/AGENTS.md: warning: - Asked", result.stdout)  # against the root's block
            self.assertIn("over one line without a pointer", result.stdout)
            self.assertNotIn("over two lines", result.stdout)  # the old entry isn't the branch's
            # A doc the branch adds must be named by the AGENTS.md it changed.
            agents.write_text(bento_block("on") + f"- {LONG} {LONG}\n- Short.\n")
            Path(tmp, "docs", "procedures").mkdir(parents=True)
            Path(tmp, "docs", "procedures", "release.md").write_text("x")
            Path(tmp, "pkg", "AGENTS.md").unlink()
            result = run("--diff", "main")
            self.assertIn("menu misses docs/procedures/release.md", result.stdout)

    def test_cli_diff_edge_cases(self):
        with tempfile.TemporaryDirectory() as tmp:
            git = lambda *a: subprocess.run(["git", "-C", tmp, *a], check=True, capture_output=True)
            git("init", "-q", "-b", "main")
            git("config", "user.email", "a@b.c")
            git("config", "user.name", "a")
            Path(tmp, "AGENTS.md").write_text(bento_block("on") + "- Base branch: `main`.\n")
            Path(tmp, "notes.md").write_text(f"- {LONG} {LONG}\n")
            Path(tmp, "howto.md").write_text("x")
            git("add", "-A")
            git("commit", "-q", "-m", "init")
            git("switch", "-q", "-c", "feature")
            run = lambda *a: subprocess.run([sys.executable, SCRIPT, *a], capture_output=True,
                                            text=True, cwd=tmp)
            # Git failing to list the branch's files fails the check instead of passing it.
            failed = run("--diff", "no-such-ref")
            self.assertNotEqual(failed.returncode, 0)
            self.assertIn("check_entries: git", failed.stderr)
            # notes.md renamed to an AGENTS.md is all new; a doc moved under docs/ must be listed.
            Path(tmp, "pkg").mkdir()
            git("mv", "notes.md", "pkg/AGENTS.md")
            Path(tmp, "docs").mkdir()
            git("mv", "howto.md", "docs/howto.md")
            Path(tmp, "AGENTS.md").write_text(Path(tmp, "AGENTS.md").read_text() + "- Lint: `make lint`.\n")
            git("commit", "-q", "-am", "moves")
            result = run("--diff", "main")
            self.assertIn("pkg/AGENTS.md: - Run the full suite", result.stdout)
            self.assertIn("menu misses docs/howto.md", result.stdout)
            # A root CLAUDE.md that imports AGENTS.md is judged against the root block.
            Path(tmp, "CLAUDE.md").write_text("@AGENTS.md\n\n- Asked to commit or open a PR: run bento-ship.\n")
            self.assertIn("CLAUDE.md: warning: - Asked", run("--diff", "main").stdout)
            # So is a proposal for a folder that doesn't exist yet.
            proposed = Path(tmp, "proposed.md")
            proposed.write_text("- Asked to commit or open a PR: run bento-ship.\n")
            result = run(str(Path(tmp, "new", "deep", "AGENTS.md")), str(proposed))
            self.assertEqual(result.returncode, 0)
            self.assertIn("may restate the bento block's", result.stdout)

    def test_cli_diff_skips_vendored_skills_and_checks_an_alias_as_its_target(self):
        with tempfile.TemporaryDirectory() as tmp:
            git = lambda *a: subprocess.run(["git", "-C", tmp, *a], check=True, capture_output=True)
            git("init", "-q", "-b", "main")
            git("config", "user.email", "a@b.c")
            git("config", "user.name", "a")
            vendor = Path(tmp, ".agents", "skills", "vendor")
            vendor.mkdir(parents=True)
            Path(vendor, "SKILL.md").write_text("x")
            Path(vendor, "AGENTS.md").write_text("# Vendor\n\nstub\n")
            Path(tmp, "docs").mkdir()
            Path(tmp, "docs", "guide.md").write_text("# Guide\n")
            Path(tmp, "CLAUDE.md").write_text("# Repo\n\nold rules\n")
            git("add", "-A")
            git("commit", "-q", "-m", "init")
            git("switch", "-q", "-c", "feature")
            run = lambda *a: subprocess.run([sys.executable, SCRIPT, *a], capture_output=True,
                                            text=True, cwd=tmp)
            # A skill update rewrites the vendored AGENTS.md: not this repo's instruction layer.
            Path(vendor, "AGENTS.md").write_text(f"# Vendor\n\n- {LONG} {LONG}\n")
            git("commit", "-q", "-am", "skills update")
            result = run("--diff", "main")
            self.assertEqual((result.returncode, result.stdout), (0, ""))
            # CLAUDE.md turned into an alias, its new AGENTS.md target still untracked: the
            # alias sorts first, and the target still gets its menu check.
            Path(tmp, "AGENTS.md").write_text("# Repo\n\n## Docs\n\n- nothing listed\n")
            Path(tmp, "CLAUDE.md").unlink()
            Path(tmp, "CLAUDE.md").symlink_to("AGENTS.md")
            git("add", "CLAUDE.md")
            git("commit", "-q", "-m", "alias")
            result = run("--diff", "main")
            self.assertEqual(result.returncode, 1, result.stdout)
            self.assertIn("AGENTS.md: menu misses docs/guide.md", result.stdout)
            self.assertNotIn("vendor", result.stdout)

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
            self.assertIn("move it to pkg/AGENTS.md (new: with a CLAUDE.md beside it, like the repo's others)",
                          result.stdout)
            self.assertIn("unless every task needs it", result.stdout)
            # Only the repository's root AGENTS.md warns: a nested one is already the cheap home.
            subprocess.run(["git", "init", "-q", tmp], check=True)
            Path(tmp, "pkg", "sub").mkdir()
            proposed.write_text("- In sub/, run `make` before sub/test.sh.\n")
            result = subprocess.run([sys.executable, SCRIPT, Path(tmp, "pkg", "AGENTS.md"), proposed],
                                    capture_output=True, text=True)
            self.assertNotIn("warning:", result.stdout)


if __name__ == "__main__":
    unittest.main()
