import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from push_gate import (FIX_SUBJECT, MESSAGE, NO_SHIP, OPEN_STEPS, SHIP_STEPS, gated_dirs, hook_command,
                       install, problem, reviewed, uninstall)

SCRIPT = Path(__file__).resolve().parent / "push_gate.py"
SHIP_SKILL = Path(__file__).resolve().parents[2] / "bento-ship/SKILL.md"
OLDEST = (3, 9)  # the macOS system python3


def oldest_python():
    """An interpreter of the oldest supported version, or None."""
    for exe in (shutil.which(f"python{OLDEST[0]}.{OLDEST[1]}"), "/usr/bin/python3"):
        if exe and Path(exe).exists():
            version = subprocess.run([exe, "-c", "import sys; print(*sys.version_info[:2])"],
                                     capture_output=True, text=True).stdout.split()
            if tuple(map(int, version)) == OLDEST:
                return exe
    return None


def git(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, text=True).stdout.strip()


class GatedDirsTest(unittest.TestCase):
    def test_finds_push_and_pr_create(self):
        self.assertEqual(gated_dirs("git push -u origin HEAD", "/r"), ["/r"])
        self.assertEqual(gated_dirs("git -C sub -c x=y push", "/r"), ["/r/sub"])
        self.assertEqual(gated_dirs("cd /a && git status&&gh pr create --fill", "/r"), ["/a"])
        self.assertEqual(gated_dirs("bash -lc git push origin", "/r"), ["/r"])
        self.assertEqual(gated_dirs("git commit -F - <<'EOF'\nIt's done\nEOF\ngit push", "/r"), ["/r"])
        self.assertEqual(gated_dirs('bash -lc "cd sub && git push"', "/r"), ["/r/sub"])
        self.assertEqual(gated_dirs("eval 'gh pr create --fill'", "/r"), ["/r"])
        self.assertEqual(gated_dirs("(cd /tmp); git push", "/r"), ["/r"])
        self.assertEqual(gated_dirs('cd /t && printf "(" && cd /a && printf ")" && git push', "/r"), ["/a"])
        self.assertEqual(gated_dirs('git -C "my dir" push', "/r"), ["/r/my dir"])

    def test_ignores_other_commands(self):
        self.assertEqual(gated_dirs('git commit -m "push it"', "/r"), [])
        self.assertEqual(gated_dirs("git log --grep push; gh pr view", "/r"), [])

    def test_heredoc_text_is_not_a_command(self):
        regex = "python3 - <<'EOF'\nhits = re.search(r\"git push|gh pr create\", l)\nEOF"
        self.assertEqual(gated_dirs(regex, "/r"), [])
        self.assertEqual(gated_dirs("cat > f <<EOF\nit's git push time\nEOF", "/r"), [])
        self.assertEqual(gated_dirs("cat <<-X > f\n\tgit push\n\tX\ngh pr create", "/r"), ["/r"])
        self.assertEqual(gated_dirs("bash <<'EOF'\ngit push\nEOF", "/r"), ["/r"])
        self.assertEqual(gated_dirs('cat <<< "git push"', "/r"), [])


class ReviewedTest(unittest.TestCase):
    def setUp(self):
        self.repo = Path(tempfile.mkdtemp())
        git(self.repo, "init", "-q")
        git(self.repo, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "--allow-empty", "-m", "init")

    def commit(self, subject):
        git(self.repo, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "--allow-empty", "-m", subject)

    def record(self, rev="HEAD"):
        (self.repo / git(self.repo, "rev-parse", "--git-path", "adversarial-review.head")).write_text(
            git(self.repo, "rev-parse", rev) + "\n")

    def ship(self, steps=SHIP_STEPS, rev="HEAD", outcome="done"):
        lines = [git(self.repo, "rev-parse", rev)] + [f"{step}: {outcome}" for step in steps]
        (self.repo / git(self.repo, "rev-parse", "--git-path", "bento-ship.head")).write_text("\n".join(lines) + "\n")

    def overlay(self, text):
        overlay = self.repo / ".agents/bento/bento-ship.md"
        overlay.parent.mkdir(parents=True, exist_ok=True)
        overlay.write_text(text)

    def test_needs_a_record_of_head(self):
        self.assertFalse(reviewed(str(self.repo)))
        self.record()
        self.assertTrue(reviewed(str(self.repo)))

    def test_only_the_reviews_fix_commits_may_follow(self):
        self.record()
        self.commit(FIX_SUBJECT)
        self.assertTrue(reviewed(str(self.repo)))
        self.commit("feat: unreviewed")
        self.assertFalse(reviewed(str(self.repo)))

    def test_needs_a_ship_record_of_head(self):
        self.record()
        self.assertEqual(problem(str(self.repo)), NO_SHIP)  # a review alone is a partial flow
        self.ship()
        self.assertIsNone(problem(str(self.repo)))
        self.commit("feat: later work")  # a second ship request in the same session
        self.record()
        self.assertEqual(problem(str(self.repo)), NO_SHIP)

    def test_every_step_needs_an_outcome(self):
        self.record()
        self.ship([s for s in SHIP_STEPS if s not in ("learn", "qa")])
        self.assertEqual(problem(str(self.repo)), OPEN_STEPS.format("learn, qa"))
        self.ship(outcome="skipped")  # no reason
        self.assertEqual(problem(str(self.repo)), OPEN_STEPS.format(", ".join(SHIP_STEPS)))
        self.ship(outcome="skipped (internal-only change)")
        self.assertIsNone(problem(str(self.repo)))

    def test_ship_record_does_not_replace_the_review(self):
        self.ship()
        self.assertEqual(problem(str(self.repo)), MESSAGE)
        self.assertIsNone(problem(str(self.repo), review_bypassed=True))
        self.overlay("- Pre-PR review: skip\n")
        self.assertIsNone(problem(str(self.repo)))

    def test_overlay_skip_and_non_repo(self):
        self.overlay("- Pre-PR review: skip\n")
        self.assertEqual(problem(str(self.repo)), NO_SHIP)  # skipping the review is not skipping bento-ship
        self.assertIsNone(problem(tempfile.mkdtemp()))

    def test_overlay_exempts_matching_branches(self):
        self.overlay("- Pre-PR review: always\n")
        git(self.repo, "switch", "-q", "-c", "nightshift/run-42")
        self.assertIsNotNone(problem(str(self.repo)))  # no preference line: gated
        self.overlay("- Pre-PR review: always\n- Pre-PR review gate: except nightshift/*\n")
        self.assertIsNone(problem(str(self.repo)))
        git(self.repo, "switch", "-q", "-c", "feature/x")
        self.assertIsNotNone(problem(str(self.repo)))
        self.overlay("- Pre-PR review gate: except nightshift/*, renovate/*\n")
        git(self.repo, "switch", "-q", "-c", "renovate/deps")
        self.assertIsNone(problem(str(self.repo)))
        git(self.repo, "switch", "-q", "nightshift/run-42")
        self.assertIsNone(problem(str(self.repo)))
        git(self.repo, "switch", "-q", "--detach")
        self.assertIsNotNone(problem(str(self.repo)))

    def test_unreadable_overlay_fails_open(self):
        overlay = self.repo / ".agents/bento/bento-ship.md"
        overlay.parent.mkdir(parents=True)
        overlay.write_bytes(b"- Pre-PR review: always\n\xff\n")
        self.assertIsNone(problem(str(self.repo)))

    def test_bento_ship_names_every_step(self):
        text = SHIP_SKILL.read_text()
        self.assertIn("bento-ship.head", text)
        for step in SHIP_STEPS:
            self.assertIn(f"`{step}`", text, step)

    def run_hook(self, event, exe=sys.executable):
        """The hook's exit code and the reminder it gave the agent, if any."""
        run = subprocess.run([exe, str(SCRIPT)], input=event, capture_output=True, text=True)
        out = json.loads(run.stdout)["hookSpecificOutput"]["additionalContext"] if run.stdout.strip() else None
        return run.returncode, out

    def test_hook_reminds_without_blocking(self):
        patch = json.dumps({"tool_name": "apply_patch", "tool_input": {"command": "+git push"},
                            "cwd": str(self.repo)})
        self.assertEqual(self.run_hook(patch), (0, None))
        event = json.dumps({"tool_name": "Bash", "tool_input": {"command": "git push"}, "cwd": str(self.repo)})
        self.assertEqual(self.run_hook(event), (0, NO_SHIP))
        self.ship()
        self.assertEqual(self.run_hook(event), (0, MESSAGE))
        self.record()
        self.assertEqual(self.run_hook(event), (0, None))
        bypass = json.dumps({"tool_name": "Bash", "tool_input": {"command": "BENTO_PRE_PR_REVIEW=skip git push"},
                             "cwd": str(self.repo)})
        self.commit("feat: unshipped")
        self.assertEqual(self.run_hook(bypass), (0, NO_SHIP))  # the bypass waives the review only

    def test_hook_reminds_under_the_oldest_python(self):
        exe = oldest_python()
        if not exe:
            self.skipTest(f"no Python {OLDEST[0]}.{OLDEST[1]} found")
        event = json.dumps({"tool_name": "Bash", "tool_input": {"command": "git push"}, "cwd": str(self.repo)})
        self.assertEqual(self.run_hook(event, exe), (0, NO_SHIP))
        self.ship()
        self.assertEqual(self.run_hook(event, exe), (0, MESSAGE))


class InstallTest(unittest.TestCase):
    def test_idempotent_and_keeps_other_hooks(self):
        path = Path(tempfile.mkdtemp()) / "settings.json"
        other = {"type": "command", "command": "other.sh"}
        stale = {"type": "command", "command": "python3 old/push_gate.py"}
        path.write_text(json.dumps({"model": "x", "hooks": {"PreToolUse": [
            {"matcher": "Bash", "hooks": [other, stale]}]}}))
        self.assertEqual(install(path), "updated")
        self.assertEqual(install(path), "unchanged")
        groups = json.loads(path.read_text())["hooks"]["PreToolUse"]
        self.assertEqual(groups[0], {"matcher": "Bash", "hooks": [other]})
        self.assertEqual(len(groups), 2)
        self.assertEqual(uninstall(path), "removed")
        self.assertEqual(json.loads(path.read_text()),
                         {"model": "x", "hooks": {"PreToolUse": [{"matcher": "Bash", "hooks": [other]}]}})
        self.assertEqual(uninstall(path), "unchanged")
        empty = path.with_name("hooks.json")
        self.assertEqual(install(empty), "added")

    def test_missing_script_warns_without_blocking(self):
        command = hook_command().replace("push_gate.py", "gone.py")
        run = subprocess.run(["bash", "-c", command], input="{}", capture_output=True, text=True)
        self.assertEqual(run.returncode, 1)
        self.assertIn("rerun bento-setup", run.stderr)

    def test_crashing_script_warns_without_blocking(self):
        boom = Path(tempfile.mkdtemp()) / "boom.py"
        boom.write_text("raise TypeError('old python')\n")
        command = f"f={boom}; " + hook_command().split("; ", 1)[1]
        run = subprocess.run(["bash", "-c", command], input="{}", capture_output=True, text=True)
        self.assertEqual(run.returncode, 1)
        self.assertIn("gate failed (exit 1); rerun bento-setup", run.stderr)


if __name__ == "__main__":
    unittest.main()
