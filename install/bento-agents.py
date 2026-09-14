#!/usr/bin/env python3
"""Install/update the bento pointer block in a repo's AGENTS.md (idempotent).

For agents without a plugin loader (e.g. Codex), whose only surface is AGENTS.md.
Marker-bounded, so re-running updates the block in place instead of duplicating it.

Usage: python3 bento-agents.py [path/to/AGENTS.md]   (default: ./AGENTS.md)
Edit the AGENTS.md source, never a CLAUDE.md symlink.
"""
import re
import sys
from pathlib import Path

START = "<!-- bento:start -->"
END = "<!-- bento:end -->"

BLOCK = f"""{START}
## bento (shared agent operating layer, vendored at `.bento/`)

Agents without a plugin loader (e.g. Codex): read the target file when its trigger fires.

- Comparing models/prompts, "which variant is better?" -> `.bento/plugins/bento-core/skills/eval-blind/SKILL.md`
- Tuning a metric, stuck score, retrieval/latency -> `.bento/plugins/bento-core/skills/hillclimb/SKILL.md`
- Principles & instruction-authoring rules -> `.bento/principles/PRINCIPLES.md`, `.bento/conventions/instruction-layer.md`
{END}"""


def main() -> None:
    target = Path(sys.argv[1] if len(sys.argv) > 1 else "AGENTS.md")
    text = target.read_text() if target.exists() else ""
    if START in text and END in text:
        new = re.sub(re.escape(START) + r".*?" + re.escape(END), BLOCK, text, flags=re.S)
        action = "updated"
    else:
        new = (text.rstrip() + "\n\n" if text.strip() else "") + BLOCK + "\n"
        action = "added"
    target.write_text(new)
    print(f"bento: {action} pointer block in {target}")


if __name__ == "__main__":
    main()
