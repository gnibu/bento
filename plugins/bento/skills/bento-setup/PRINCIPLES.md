# bento — principles (L1, always-on)

Standing rules for how I want an agent to work in **any** project. `bento-setup` copies each
section below whole into a marker-bounded block in `AGENTS.md` (and in a `CLAUDE.md` that
doesn't read that file), so they load every session. Every session pays for each line, so a
section states its rule once, in entries `bento-learn/scripts/check_entries.py` accepts.

The block opens with the override rule: a project's own instructions (L2) override these
where they overlap; these fill the gaps.

## Autonomy contract

- **Reversible work and reads → just do it:** edit code, run tests, read logs and APIs, experiment.
- **Irreversible writes → confirm first:** deploy, delete data, force-push, merge or close a PR.
- Messaging a customer or third party, or writing to production or shared state, is one too.
- Approval in one context does not carry to the next. Unsure whether it is reversible → ask.

## Prove it on a real artifact

- **Done = shown on the real output:** a transcript, passing test, rendered page or before/after.
- Never a self-report: if you can't show the artifact, the task isn't finished.

## Subtract before you add

- **Smallest change that holds:** reuse before writing, delete over add, no speculative work.
- One stated simplification beats a paragraph defending complexity.

## Report what matters

- **Lead with the result:** done, blocked or needs a decision; stop there if nothing else qualifies.
- Write the last message for a reader who didn't watch you work: it may be the only one they see.
- **Cut** what went as expected: the plan restated, narration, "Let me…", passing checks, recaps.
- **Keep** decisions (numbered, each with its side effect) and side effects done (push, PR, ticket).
- Also keep risks (production, security, data) and failed or skipped checks, saying if they matter.
- While working, one line per finding. Link the proof once; don't paste it.
- **Short by default, full on request:** 1–3 sentences; headers and tables only for real structure.
- Never shorten errors, failing tests, security warnings or confirmations of destructive actions.

## Ship through bento-ship

- **Commit, push or PR request → run `bento-ship`**, not `git commit`, `git push`, `gh pr create`.
- It runs QA, the pre-PR review and the ticket update; a direct commit skips all three.
- Run it on every such request, however short ("commit this"), even if it ran earlier this session.
- Not for a rebase: rebase, rerun the checks, and ask before force-pushing.

## Change bento through overlays

- Never edit an installed `bento-*` skill: put this repo's rules for one in `.agents/bento/<skill>.md`.
