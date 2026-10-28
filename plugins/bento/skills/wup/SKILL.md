---
name: wup
description: |
  Very short status of the current work: what's done, what's next, what the user must do.
  Use when the user types /wup or asks "what's up", "where are we", "status?", "catch me up".
  Reads state only; changes nothing.
---

# What's up

Tell the user where the work stands in a few lines they read at a glance.

**Repo layer first.** Read the repo's `AGENTS.md`/`CLAUDE.md` and, if it exists,
`.agents/bento/wup.md`, under the
[overlay rules](../bento-learn/references/instruction-layer.md#repo-overlays-for-bento-skills).
The format in step 3 is a default: the overlay, or the repo's own reporting rules (verdict
first, fixed headings, a line cap), replace its headings and length. Steps 1–2 and the
guardrails still apply.

## Steps

1. **Check the real state.** Re-read this conversation, then the branch: `git status`,
   `git log --oneline <base>..HEAD`, and the open PR and its checks if there is one. Trust
   what these show over what you remember.
2. **Name the task.** Find the high-level goal the thread works toward, not the step you are
   on: the ticket or PR title if there is one, else the user's first request in a few words.
3. *(default)* **Answer with the task as a title, then exactly three headings**, one to
   three bullets each, a few words per bullet:

   ```
   🎯 **<the high-level task>**

   ✅ **Done**
   - <finished and proven, with a pointer: commit, PR, file>

   🤖 **Next**
   - <what you, the agent, will do next, in order>

   👉 **You**
   - <what only the user can do: a decision, an approval, a login, a review>
   ```

   Keep the emojis on the title and headings only; none in the bullets. 🤖 marks the
   agent's work, 👉 the user's.

   Write `- nothing` under a heading with nothing to say.

## Guardrails

- Read only: run no edits, commits, pushes or tests to produce the report.
- Say done only for what was checked; list unverified work under **Next**.
- No preamble, recap or closing line around the report.
