# Monitoring-driven error fix

Fix one reproducible root cause from a bounded set of monitoring issues. The repository or
caller supplies the provider, projects/environment, time window and candidate limit.

1. Fetch the supplied candidate set and rank impact: affected users, then severity of the
   broken path, then event count. Record the evidence for that order. Check open PRs and both
   open and closed tickets. An issue is owned only by an open PR, an open ticket, a closed
   ticket with no events since it closed, or a ticket a person canceled or declined, whatever
   its events. A closed ticket with newer events makes the issue a candidate again, as a
   possible regression. Skip issues that are owned, outside scope or impossible for repository
   code to prevent. Read the actual event/trace, not just its title. Missing monitoring access
   is a blocker, not a no-op.
2. Use `bento-investigate` in work-only context: reproduce, capture inputs/stack, trace the
   shared cause, test one hypothesis, fix it and add a regression test seen failing without
   the fix. A candidate requiring a production write, a public-contract decision or an
   out-of-scope change is disqualified; examine the next candidate and record the reason.
3. Expected/recovered failures can be actionable noise only when code proves recovery and no
   user-visible failure remains. Trace the emitter and the monitoring integration. Never hide
   exhausted retries, lost data or a real failure with a broad message filter. An intentionally
   monitored condition stays unless changing that policy was authorized. For a suppression,
   test both the recovered case not being reported and the real failure still being reported;
   for grouping, test that differing incidental values share a fingerprint.
4. Keep the fix small (about 80 changed lines by default) and at the root cause. Run the area's
   checks and regression. Report the selected issue id/link, impact, immediate/root cause,
   evidence, fixed behavior, any closed ticket as a possible regression, and every skipped
   candidate as the [result contract](../SKILL.md#result-contract) lists it, with the first
   reason that applies:
   - `owned`: step 1's owner holds it.
   - `regressed_after_close`: a closed ticket with newer events, not fixed in this run.
   - `out_of_scope`: outside the assignment, or the fix needs an out-of-scope change.
   - `not_preventable`: repository code cannot prevent it.
   - `needs_person`: its code cannot prove the root cause, or it needs a production write, a
     public-contract decision or an unavailable environment.
   - `intentional`: an intentionally monitored condition, with no authorized policy change.

   A candidate ranked below the fixed one with none of these was not examined: leave it out.
   Do not resolve, assign, ignore or comment on monitoring issues, or create or reopen tickets;
   the caller handles external state and delivery.
