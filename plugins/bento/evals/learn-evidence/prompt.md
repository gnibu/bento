---
max_turns: 3
timeout_seconds: 300
allowed_tools: [Skill, Read]
---

This is a hypothetical planning exercise, not a repository on disk. Do not inspect
the working directory, search for files, or execute commands. Consult the relevant
available bento command/skill if present, then answer in at most 350 words. If bento
is unavailable, use your own judgment without searching for it.

I'm about to open a PR and want to capture learnings with bento's learn step. The
branch's session digest includes an earlier learn run, which listed these proposals:

1. AGENTS.md: "Run `just mypy <file>` from backend/, never plain mypy."
2. AGENTS.md: "`supabase db push` fails with `permission denied for schema auth`
   unless you pass `--linked`." From `~/.claude/projects/-work-app/3f2a.jsonl`,
   operator turn: "use --linked, it always fails without it".
3. ship skill: "Always run the full e2e suite before pushing."
4. docs/api.md: "The staging API needs `X-Env: staging`." From a 400 error in
   `~/.codex/sessions/2026/09/20/rollout-9c1.jsonl`.

(For context: docs/api.md in the current repo already has a section on `X-Env`.)

Draft the proposals I should review for approval, in the exact format you would
show them. Don't edit anything.
