# Eval cases

- The eval sandbox has no network: a case whose skill needs packages installs them in `setup.sh` (see `hotspots-scan`).
- `_fixtures/repo.sh` leaves its commits on `eng-42-greeting`; a case working from `origin/master` merges and pushes them there.
- A failed run's tool calls are only in its `out/trace.jsonl`, kept with `--keep-temp`; the results JSON holds the final answer.
- `--json <file>` puts runs under `cases[].arms.with[]`, each with `graders[].passed`.
- Haiku judges misgrade long answers: recheck a failed `llm` grader with `--judge-model sonnet`.
