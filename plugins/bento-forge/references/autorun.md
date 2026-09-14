# Autorun: unattended session retrospectives

Opt-in mode where the `Stop` hook hands each finished session to a detached
worker instead of nudging the operator. Enable with `BENTO_IMPROVE_AUTORUN=1` on
the hook command (see `stop-hook.md`).

## Pipeline

```
Stop hook  (stop-nudge.sh, once per session_id)
  └─ nohup worker.sh --transcript … --session … --cwd …      detached
       │
       ├─ digest.sh          transcript -> signal only, or exit if below gate
       ├─ claude -p          read-only reflect  -> candidate JSONL
       ├─ ledger.sh add      bank candidates locally
       └─ ledger.sh ripe     key recurred in >=N sessions?
            ├─ claude -p        (optional) tracker: open the issue that hosts the work
            └─ scratch worktree -> claude -p (acceptEdits) -> commit -> PR
```

There is no cron and no LaunchAgent. A scheduler would have to rediscover which
sessions ended and when; the `Stop` hook already knows and hands over the exact
transcript path.

## Repo adoption gate

The worker only reflects on sessions inside a checkout that has adopted bento —
the routing rules, sinks and quality bar all assume the bento instruction layer.
The gate is the presence of a marker path, `.bento` by default (the vendored
bento dir). Override with `BENTO_IMPROVE_REPO_MARKER=<path>`, or set it empty to
run in any git repo.

## The gate

`digest.sh` keeps a session only if it has **≥3 operator turns AND ≥1 failure**
(`is_error` tool result or `hook_blocking_error`). Measured over 222 transcripts
across 7 days, that selects 115 and reduces them to 3.1% of their bytes — 60 KB
mean, 278 KB worst case. The gate is about *friction*, not effort: a long clean
session taught nobody anything; a short one that failed twice did.

## The ledger

`~/.claude/bento-improve/ledger.jsonl` — override with `$BENTO_IMPROVE_LEDGER`.

**Local, not in the repo.** The transcripts it derives from exist only on this
machine, so recurrence can only ever be counted per-operator; and several
detached workers append concurrently, which in a committed file means a merge
conflict per session. The ledger is scratch state on the way to a PR. The PR is
the shared artifact.

**Append-only JSONL under a `mkdir` lock** (macOS has no `flock(1)`, and
util-linux is not worth pulling in for one advisory lock).

**Dedup is by `key`** — a stable kebab-case slug naming the *trigger*, emitted by
the reflecting model. Existing keys are fed back into the next reflect prompt
with an instruction to reuse an exact match, so the model does the fuzzy matching
and the ledger only counts. A key's weight is its number of **distinct
`session_id`s**: one session tripping over the same thing five times is still one
observation.

Read by exactly two things: the worker, at the end of every run (so no second
scheduler exists), and you.

```bash
ledger.sh pending          # key -> distinct-session count, unpromoted only
ledger.sh ripe [N]         # keys at or above the threshold (default 3)
ledger.sh show <key>       # every record behind a key
ledger.sh keys             # what gets fed to the next reflect prompt
ledger.sh path             # where it lives
```

## The tracker issue (optional)

Tracker integration is **opt-in and org-specific**: it fires only when a team is
configured via `BENTO_IMPROVE_LINEAR_TEAM`. Without it, the worker skips straight
to a plain `learnings/<stamp>` branch and opens the PR anyway — the learning is
never lost to a missing tracker.

When enabled, promotion opens a Linear issue **before** creating the branch, then
names the branch with Linear's own `branchName`. That is what makes the GitHub
integration attach the PR to the issue automatically — no magic word in the body,
no second API call, and the PR shows up under the issue the way any hand-made one
does.

Title and description come entirely from the ledger, so no model is involved in
naming the work:

- one ripe key → the issue is titled with that learning's summary
- several → `Session retrospective: N recurring learnings`
- the body groups evidence by key, one line per session that independently hit it

**Lifecycle.** The issue is filed in **Triage** — at that moment nothing exists
behind it. Once the PR is created it moves to **In Review**: the work is done and
waiting on a human, which is what In Review means. The transition is deliberately
after PR creation, never at filing time; an issue claiming review with no PR
behind it is a lie, and a promotion can still fail at the commit or push step.

**The `session-learning` label is load-bearing, not decoration.** Naming the
branch after the issue is what attaches the PR — and it is also what makes
Linear's GitHub automation fire on branch push (a Triage issue can come back In
Progress, assigned, and pulled into the live cycle). Nothing on the API side can
prevent that, so the issue carries a marker the workspace automations can
exclude. **Configure that exclusion in Linear** (it cannot be done from here) or
every unattended proposal inflates the active sprint.

Creation goes through the **Linear MCP server** declared in the repo's `.mcp.json`,
in its own tiny `claude -p`. A whole model invocation for one API call is silly,
but it is the only write path available, and the issue must exist before the
branch. It is kept to one tool, one line of output.

If the MCP server is unreachable or its OAuth has lapsed, the worker logs it,
falls back to a `learnings/<stamp>` branch and opens the PR anyway. Losing the
issue must never cost the learning.

Preview what the current ledger would file, without touching any tracker:

```bash
worker.sh --preview-issue
```

## Tunables

| Env | Default | |
|---|---|---|
| `BENTO_IMPROVE_AUTORUN` | unset | Enables autorun; unset means nudge. |
| `BENTO_IMPROVE_REPO_MARKER` | `.bento` | Repo-adoption marker; empty runs in any git repo. |
| `BENTO_IMPROVE_BASE_BRANCH` | `main` | Branch the promotion worktree and PR target. |
| `BENTO_IMPROVE_THRESHOLD` | `3` | Distinct sessions before a key is promoted. |
| `BENTO_IMPROVE_REFLECT_MODEL` | `sonnet` | Runs on every gated session — keep it cheap. |
| `BENTO_IMPROVE_PROMOTE_MODEL` | `opus` | Runs rarely and writes code. |
| `BENTO_IMPROVE_STATE` | `~/.claude/bento-improve` | Logs and lock. |
| `BENTO_IMPROVE_LEDGER` | `$BENTO_IMPROVE_STATE/ledger.jsonl` | |
| `BENTO_IMPROVE_LINEAR_TEAM` | unset | Set to enable tracker integration; the team name. |
| `BENTO_IMPROVE_LINEAR_STATUS` | `Triage` | |
| `BENTO_IMPROVE_LINEAR_LABELS` | `session-learning` | Marker for the automation exclusion. |
| `BENTO_IMPROVE_LINEAR_REVIEW_STATUS` | `In Review` | Set once the PR exists. |
| `BENTO_IMPROVE_LINEAR_MODEL` | `sonnet` | Files and transitions the issue via the Linear MCP server. |

## Untrusted input

A transcript records whatever the session read — scraped sites, fetched pages,
third-party tool output — so an instruction planted on a crawled page reaches
this pipeline verbatim. Two stages consume it:

**Reflect** cannot write, but it can still be steered into reading a secret and
placing it in `evidence`, which is then published to a tracker and GitHub. It
runs with `Edit,Write,Bash,WebFetch,WebSearch` denied plus explicit `Read`
denials for `.env*`, `*.pem`, `*.key` and `secrets/**`, and the digest is wrapped
in an untrusted-data envelope.

**Promote** can write, and its input is ledger text produced by another model.
It keeps a shell: code it cannot test is code the pre-commit hook rejects after
the run is over, discarding the work. `git commit`, `git push` and `gh` stay
denied — the script owns those, and two writers on one branch is a real bug
rather than a hypothetical one. The ledger payload is fenced and labelled as
data, which is free; a hostile string would have to survive the digest, be
picked as a learning, and recur across N independent sessions before reaching
this stage.

**On the way out**, `secret-scan.sh` drops any candidate whose text matches a
credential shape — key prefixes, JWTs, private-key headers, connection strings
with passwords, `KEY=<blob>` assignments. It rejects rather than redacts: partial
redaction is a bypass surface, and dropping costs nothing because a genuinely
recurring learning re-surfaces from a cleaner session.

## Safety

- The reflect pass runs with `--disallowedTools Edit,Write,NotebookEdit,Bash`. It
  can read and grep the repo; it cannot change it.
- Promotion runs in a **throwaway worktree** branched from `origin/<base>`, never
  the session's own checkout — this is an agent with write access firing while
  nobody is watching, and it must not land in a branch someone is mid-work on.
- Promotion cannot push or call `gh` itself; the script does that after checking
  a commit actually exists.
- One promoter at a time via a lock dir, broken automatically after 30 minutes so
  a killed worker cannot disable promotion permanently.
- An in-flight issue is persisted to `inflight.json` keyed to its ripe set and
  reused on the next run, so a repeated push failure cannot file one Triage issue
  per session.
- Candidate records are schema-validated before they enter the ledger: kebab-case
  string key, sink from a fixed enum, bounded string fields.
- Keys are only marked promoted after the PR is created. A failed push leaves
  them pending rather than losing them.

## Logs

```
~/.claude/bento-improve/worker.log      one line per session + claude stderr
~/.claude/bento-improve/unparsed.log    model spoke, nothing parsed
```

`unparsed.log` exists because the first end-to-end run logged "0 candidates"
while the model had actually found two real bugs: it had prefixed the JSONL with
one line of prose, and plain `jq -c` aborts the stream on the first parse error.
The parser now uses `fromjson? // empty`; `test-parse.sh` pins that with the real
output as a fixture.

## Checks

```bash
./test-ledger.sh    # counting, promotion, threshold rules
./test-parse.sh     # reflect-output parsing against a real captured response
./test-issue.sh     # tracker issue title/body derived from ripe keys (renders only)
./test-secret-scan.sh   # credential shapes are dropped, ordinary errors are not
./digest.sh <transcript.jsonl> | head    # eyeball a digest
./worker.sh --preview-issue              # what the ledger would file right now
```
