# Autorun: unattended session retrospectives

The loop is split across two hooks by what each can do — **bank at Stop, surface
at SessionStart** — so it needs no env var and works the same on Claude and
Codex. See `stop-hook.md` for wiring.

- **Stop (`session-stop.sh`)** stores a durable pending job, debounces per-turn
  Stop events until the session has been quiet, then hands the complete transcript
  to a detached worker that reflects + banks candidates. It never opens a PR.
- **SessionStart (`session-start.sh`)** re-arms pending jobs whose detached process
  was lost, then reads the ledger (no LLM) and injects a model-visible prompt for
  every valid candidate by default. It also periodically instructs the agent to
  check for a newer Bento version
  and offer a manual update only when one is confirmed. The hook itself uses no
  network; a local timestamp throttles these checks. Worker children inherit
  `BENTO_UPDATE_REMINDER_DAYS=0`, so they cannot consume the reminder window.
  This is where surfacing happens: SessionStart `additionalContext` is
  model-visible, a Stop hook's is not.
- **PR opening is opt-in.** By default the human's yes to the SessionStart prompt
  is the approval gate. Set `BENTO_IMPROVE_AUTO_PR=1` on the Stop command for a
  fully hands-off worker that opens the PR itself once a learning ripens.

## Pipeline

```
Stop hook  (session-stop.sh, durable enqueue; later bursts update generation)
  └─ pending-session.sh -> quiescence -> worker.sh             detached
       │
       ├─ digest.sh          Claude/Codex transcript -> signal, or exit below gate
       ├─ claude -p          read-only reflect  -> candidate JSONL
       ├─ ledger.sh add      bank candidates locally           ← default stops here
       └─ ledger.sh ripe     key recurred in >=N sessions?     ← only if BENTO_IMPROVE_AUTO_PR=1
            ├─ claude -p        (optional) tracker: open the issue that hosts the work
            └─ scratch worktree -> claude -p (acceptEdits) -> commit -> PR

SessionStart hook  (session-start.sh, next session)
  ├─ pending-session.sh recover -> re-arm jobs without a live waiter
  └─ ledger.sh ripe 1 -> inject a model-visible "N candidates ready" prompt
```

There is no cron and no LaunchAgent. The `Stop` hook already knows the exact
transcript path, so it records the handoff under
`$BENTO_IMPROVE_STATE/pending/`. The detached waiter is the fast path;
SessionStart is the recovery path after a killed process or reboot. Recovery is
also detached, so a recovered candidate appears after reflection completes and
is surfaced by a later SessionStart.

## Trivial-session skip

`session-stop.sh` first skips transcripts that cannot yet teach anything: a
missing transcript, or **fewer than 2 operator turns AND no tool use**. The cheap
check understands both Claude and Codex transcript schemas and sets no permanent
state, so a later richer turn is reconsidered. Once substantive, Stop events are
debounced until `BENTO_IMPROVE_QUIESCE_SECS` of inactivity; the worker then sees
the complete transcript. A later burst re-arms reflection. The `digest.sh` gate
inside the worker remains the real quality filter.

## Repo adoption gate

The worker only reflects on sessions inside a checkout that has adopted bento —
the routing rules, sinks and quality bar all assume the bento instruction layer.
The gate is the presence of a marker path, `.bento` by default (the vendored
bento dir). Override with `BENTO_IMPROVE_REPO_MARKER=<path>`, or set it empty to
run in any git repo.

## The gate

`digest.sh` keeps a session only if it has **≥3 operator turns AND ≥1 failure**
(`is_error`/failed tool result or `hook_blocking_error`). Measured over 222 transcripts
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

Read by three things: the worker (when `BENTO_IMPROVE_AUTO_PR=1`, to decide what
to promote), `session-start.sh` at the next session start (to surface candidates
for human review), and you.

```bash
ledger.sh pending          # key -> distinct-session count, excluding closed keys
ledger.sh ripe [N]         # keys at or above the threshold (default 3)
ledger.sh show <key>       # every record behind a key
ledger.sh keys             # what gets fed to the next reflect prompt
ledger.sh dismiss <key>    # permanently hide a rejected candidate
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
| `BENTO_IMPROVE_AUTO_PR` | unset | Set on the Stop command for a hands-off worker that opens the PR itself once a learning ripens. Unset = bank only, surface at next SessionStart. |
| `BENTO_IMPROVE_QUIESCE_SECS` | `300` | Idle window after the latest Stop event before the complete transcript is reflected. |
| `BENTO_IMPROVE_SURFACE_THRESHOLD` | `1` | Distinct sessions before a candidate is shown for human review at SessionStart. |
| `BENTO_IMPROVE_REPO_MARKER` | `.bento` | Repo-adoption marker; empty runs in any git repo. |
| `BENTO_IMPROVE_BASE_BRANCH` | `main` | Branch the promotion worktree and PR target. |
| `BENTO_IMPROVE_THRESHOLD` | `3` | Distinct sessions before unattended auto-promotion. It does not delay human review. |
| `BENTO_IMPROVE_REFLECT_MODEL` | `sonnet` | Runs on every gated session — keep it cheap. |
| `BENTO_IMPROVE_PROMOTE_MODEL` | `opus` | Runs rarely and writes code. |
| `BENTO_IMPROVE_STATE` | `~/.claude/bento-improve` | Logs and lock. |
| `BENTO_IMPROVE_LEDGER` | `$BENTO_IMPROVE_STATE/ledger.jsonl` | |
| `BENTO_UPDATE_REMINDER_DAYS` | `30` | Interval between update-check instructions at SessionStart, starting on first use. `0` disables without touching the timestamp. The worker always exports `0` for its children; use `0` for other unattended callers too. |
| `BENTO_UPDATE_REMINDER_STATE` | `~/.bento/update-reminder` | Local throttle timestamp shared across agents and workspaces; separate from the learning ledger and worker state. |
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
- Pending analyses are persisted under `BENTO_IMPROVE_STATE`; SessionStart
  atomically re-arms dead jobs. A job is removed after a successful worker
  handoff or when its transcript/workspace no longer exists and retry cannot help.
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
./test-ledger.sh    # counting, promotion, dismissal, threshold rules
./test-parse.sh     # reflect-output parsing against a real captured response
./test-issue.sh     # tracker issue title/body derived from ripe keys (renders only)
./test-secret-scan.sh   # credential shapes are dropped, ordinary errors are not
./test-session-stop.sh  # Stop hook skips trivial sessions, spawns on substantive ones
./test-pending-session.sh # retry/recovery, invalid-job cleanup, signal-safe locking
./test-session-start.sh # candidate surfacing, update checks, worker children preserve reminder state
./digest.sh <transcript.jsonl> | head    # eyeball a digest
./worker.sh --preview-issue              # what the ledger would file right now
```
