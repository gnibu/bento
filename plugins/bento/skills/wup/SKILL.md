---
name: wup
description: |
  Very short status of the current work: what's done, what's next, what the user must do.
  Use when the user types /wup or asks "what's up", "where are we", "status?", "catch me up".
  Reads state only; changes nothing.
---

# What's up

Tell the user where the work stands in a few lines they read at a glance.

## Steps

1. **Check the real state.** Re-read this conversation, then the branch: `git status`,
   `git log --oneline <base>..HEAD`, and the open PR and its checks if there is one. Trust
   what these show over what you remember.
2. **Answer in exactly three headings**, one to three bullets each, a few words per bullet:

   ```
   ✅ **Done**
   - <finished and proven, with a pointer: commit, PR, file>

   ⏭️ **Next**
   - <what you will do next, in order>

   👉 **You**
   - <what only the user can do: a decision, an approval, a login, a review>
   ```

   Keep the three emojis on the headings only; none in the bullets.

   Write `- nothing` under a heading with nothing to say.

## Guardrails

- Read only: run no edits, commits, pushes or tests to produce the report.
- Say done only for what was checked; list unverified work under **Next**.
- No preamble, recap or closing line around the three headings.
