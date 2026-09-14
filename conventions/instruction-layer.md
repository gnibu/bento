# Convention — authoring a project's instruction layer (L2)

How to write and grow a repo's `CLAUDE.md` / `AGENTS.md` / skills / docs so agents stay
effective without the instruction surface bloating. Generalized from Rose's
`rose-session-learn` (space budget) and `claude-md-improver` (what belongs where).

The governing idea: **every line in an instruction file is a cost paid by every future
reader.** Price the sink before you write, and put each fact in its cheapest correct home.

## Sinks, by price

| Sink | Loaded | Cost | Budget per entry |
|---|---|---|---|
| Code comment / the fix itself | when that code is opened | ~free | a paragraph, if useful |
| Shared doc (guide / README) | when its linked task starts | low | as long as it earns |
| Skill (`SKILL.md`) | when its task triggers | low | a sentence per point |
| `AGENTS.md` | **every** agent working in that directory tree (root = repo-wide) | **highest** | **one bullet, ≤2 wrapped lines** |

An `AGENTS.md` line is written once and paid for indefinitely by everyone — including the
agents it will never help. The bar scales with price: fix the source when you can (a bug
fixed can't recur); otherwise pick the cheapest sink that the reader will actually hit at
the moment they need it.

## Where each fact goes

- **Code bug / wrong logic** → fix the source + a test. The fix *is* the documentation.
- **Procedure for humans and agents** → a shared doc; link it from the relevant `AGENTS.md`
  or skill with a task trigger. Don't fork an agent-only copy.
- **Agent orchestration / tool choice / review behavior** → a skill (amend the owner;
  create one only if none fits).
- **Code-scoped gotcha / command / env quirk** → the **nearest** `AGENTS.md` to that code,
  not the subsystem root. Root only for cross-cutting rules.
- **Human-facing architecture / decision** → docs (or an ADR).
- **One-off** → drop it.

## The reuse gate (before writing anything)

Ask: *"Will this recur, with a concrete trigger?"* Name the trigger and the takeaway, or
drop it. Default to dropping — storing costs context on every future agent; a missed
one-off costs nothing. Surfacing nothing is a valid outcome.

## `AGENTS.md` entries take the pointer form, nothing else

```
- **<trigger>:** <takeaway>. See <file> <symbol>.
```

Trigger = when it bites. Takeaway = what to do instead. Pointer = where the reasoning
lives. If reasoning doesn't fit in two lines, it belongs at the code site, in a shared
guide, or in a skill reference — not in `AGENTS.md`. Writing "which caused…", a ticket
number, or a second justifying sentence means you're drafting a code comment in the wrong
file. Cut to the pointer.

## Discoverability — task-triggered links

Instruction files are a routing map, not a knowledge dump. From `CLAUDE.md` / `AGENTS.md`,
**link procedures by their task trigger** ("Writing a migration → <guide>"), so the guide
surfaces exactly when the task starts and costs nothing until then. Keep the detailed
procedure in the doc; keep only the trigger + link in the instruction file.

## Skill routing needs an explicit fallback

A routing table that only lists known tasks silently drops everything else. End it with:
**no match → sequence an explicit todolist before acting, then propose capturing it as a
skill.** An off-catalog task should still get a frame, and a recurring one should become a
skill (see the skill-authoring convention / `create-skill`).

## Quality bar

- **No false comfort.** A rule that says something is "fine / normal" is valid only if the
  same observable can't also mean the failure case. "Op at 70% isn't stuck" is wrong when a
  genuinely stuck op also sits at 70% — it talks the next reader out of a real bug.
- **Right sink, terse.** Never pad an `AGENTS.md` with a lesson that isn't about that code.
- **Already covered?** If a rule exists but got ignored, that's an operator-discipline miss,
  not a doc gap — don't duplicate it.
