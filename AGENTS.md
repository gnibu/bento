# bento — repository instructions

How to change bento itself. `CLAUDE.md` is a symlink to this file.

- Work in a bento checkout, never in a consumer's `.bento` submodule or an installed plugin
  cache. Branch from `origin/master`; open one PR per change with `gh pr create --base master`.
  Commit as you go: workspace janitors can delete a worktree whose earlier PRs merged.
- bento is one plugin, `plugins/bento` (`skills/`, `commands/`, `references/`, `scripts/`,
  `evals/`); commands are `/bento:<name>`. Don't add a second plugin or a `bento-` prefix.
- Manifests carry no `version`: Claude versions the plugin by commit SHA, so every merge
  reaches `claude plugin update`. Don't add one back.
- Keep the legacy-name handling in `install/` (`bento-core`, `bento-forge`, `session-stop.sh`);
  it migrates older consumer installs.

## Verify before the PR

- `python3 -m unittest discover -s install -p 'test_*.py'`
- `python3 -m unittest discover -s plugins/bento/scripts -p 'test_*.py'` and
  `bash plugins/bento/scripts/test-session-start.sh`
- Skill or reference edits: run `claude plugin eval plugins/bento --case <case> --runs 3
  --judge-model sonnet --no-publish` on a checkout before the edit and one after, and keep
  the edit only for a lift beyond run-to-run noise. Prefer `regex` graders; `llm` judges
  are noisy, and a no-tools case can't be failed for checks it was told not to run.

## After merge

Consumers update in a separate PR: bump the `.bento` pin, rerun `bash .bento/install.sh` from
the main checkout (or `claude plugin marketplace update bento` then
`claude plugin update bento@bento --scope user|project`), and restart the agent.
