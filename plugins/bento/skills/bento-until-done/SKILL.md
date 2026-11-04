---
name: bento-until-done
description: |
  Drive one task or ticket to a checkable finish condition without stopping early: change
  approach when one fails, never relax the goal, stop only when the check passes or at a dead
  end written up. Use when the user wants it finished, not a first attempt. Triggers: "until
  done", "keep going until", "don't stop until", "try harder", "see it through", "run until
  green", "work this ticket to a PR". A metric with no target → bento-hillclimb. Scheduled or
  unattended work → the repo's factory.
---

# Until done

The failure mode: the first attempt fails, or half works, and the agent reports what it tried,
quietly shrinks the goal, or stops to ask. Trying harder comes from a check that can only pass
or fail, and from having no other way to finish.

**Repo layer first.** Read the repo's `AGENTS.md`/`CLAUDE.md` and, if it exists, the
overlay `.agents/bento/bento-until-done.md` at the repo root; follow it under the
[overlay rules](../bento-learn/references/instruction-layer.md#repo-overlays-for-bento-skills).

## Steps (paste as todos)

1. **Write the finish condition before changing anything:** a check you can run that passes or
   fails, such as a test, a command's output, or a page's real state. The user's `--until
   "<condition>"` or the ticket's acceptance criteria come first. "Spend an hour on it" is not
   a condition. None you can derive → ask once, then wait.
2. **Run it now and record the result.** Already passing → say so and stop.
3. **One change per iteration.** Make the smallest change the evidence supports, run the check,
   commit if it moved, discard if it didn't. Log one row each time: what changed, what the check
   showed, kept or discarded.
4. **A failure means find out why, then do something different.** Never run the same approach
   twice. A cause you can't explain → `bento-investigate`. Something blocking the goal that you
   can fix (a flaky check, broken tooling, a related bug) is yours to fix; keep unrelated work
   out of the diff.
5. **Keep the goal fixed.** Never skip or loosen a test or check, mock the surface the condition
   names, or drop part of what was asked. A goal that really must change is the user's call.
6. **Settle reversible choices yourself** and log them. Ask only for an irreversible action or a
   product call no run can settle.
7. **Stop at a dead end, and say it's one.** After three materially different approaches fail,
   or a blocker you can't remove (missing access, an outage, a contradiction in the ask), stop:
   the condition, not met, each approach and what it showed, the blocker, what you recommend and
   the options.
8. **Finish on the real check.** It passes on the final commit, run now, not remembered. A ticket
   or a request for a PR → `bento-ship`: naming the ticket is the request for its PR. Otherwise
   report and stop.

**Report:** the condition and its final result, iterations run, what landed, what was discarded
and why.

## Guardrails

- "Not done" is an honest outcome; a green result from a weakened check is not.
- No duration counts as progress: a check that hasn't moved after three approaches is a dead end.
- The autonomy contract still holds: persistence never authorizes an irreversible write.
