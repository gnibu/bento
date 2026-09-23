# AGENTS.md: always-on principles and legacy fallback

Current Codex supports native skills. Install Bento's relative skill links with:

```bash
bash .bento/install.sh --codex
```

Bento playbooks appear as `bento:<name>`; setup and improve share their instructions
with the Claude commands. Start a fresh Codex session after setup.

The marker-bounded `AGENTS.md` block remains the always-on principles layer and a legacy
fallback for agents that do not discover skills. Principles are distilled and inlined from
`principles/PRINCIPLES.md`; fallback playbooks stay task-triggered pointers into `.bento/`.

```bash
python3 .bento/install/bento-agents.py ./AGENTS.md
```

`/bento:setup` runs this for you. The authoritative generated block lives in
`install/bento-agents.py`. Re-running updates only the `<!-- bento:start -->` through
`<!-- bento:end -->` block, preserving surrounding project instructions. Edit the `AGENTS.md`
source, never a `CLAUDE.md` symlink. Review this committed change before landing it.
