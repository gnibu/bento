#!/usr/bin/env python3
"""Install/update the bento pointer block in a repo's AGENTS.md (idempotent).

For agents without a plugin loader (e.g. Codex), whose only surface is AGENTS.md.

Principles are always-on: they are INLINED (distilled from principles/PRINCIPLES.md, the
single source) so they stay resident every task — a pointer would only be a suggestion to
fetch. Playbooks are on-demand: they stay pointers, since their trigger says when to read.

Marker-bounded, so re-running updates the block in place instead of duplicating it.
Usage: python3 bento-agents.py [path/to/AGENTS.md]   (default: ./AGENTS.md)
Edit the AGENTS.md source, never a CLAUDE.md symlink.
"""
import re
import sys
from pathlib import Path

START = "<!-- bento:start -->"
END = "<!-- bento:end -->"
BENTO = Path(__file__).resolve().parent.parent  # bento root (parent of install/)


def distill_principles() -> list[tuple[str, str]]:
    """Each `## Heading` + its `> summary` line, from principles/PRINCIPLES.md.

    The `> ...` blockquote right after a heading is the deliberate one-line summary; fall
    back to the first sentence of prose if a section has none.
    """
    text = (BENTO / "principles" / "PRINCIPLES.md").read_text()
    out = []
    for m in re.finditer(r"^## (.+?)\n+(.+?)(?:\n\n|\Z)", text, flags=re.M | re.S):
        heading = m.group(1).strip()
        body = m.group(2).strip()
        if body.startswith(">"):
            summary = body.splitlines()[0].lstrip("> ").strip()
        else:
            summary = re.split(r"(?<=\.)\s", " ".join(body.split()), maxsplit=1)[0]
        out.append((heading, summary.rstrip(".")))
    return out


def build_block() -> str:
    principles = "\n".join(f"- **{h}:** {s}." for h, s in distill_principles())
    return f"""{START}
## bento (shared agent operating layer, vendored at `.bento/`)

**Always-on principles — apply to every task, no exceptions:**

{principles}

**Read the file when its trigger fires:**

- Comparing models/prompts, "which variant is better?" -> `.bento/plugins/bento-core/skills/eval-blind/SKILL.md`
- Tuning a metric, stuck score, retrieval/latency -> `.bento/plugins/bento-core/skills/hillclimb/SKILL.md`
- Authoring instruction files, capturing learnings -> `.bento/conventions/instruction-layer.md`
{END}"""


def main() -> None:
    target = Path(sys.argv[1] if len(sys.argv) > 1 else "AGENTS.md")
    block = build_block()
    text = target.read_text() if target.exists() else ""
    if START in text and END in text:
        new = re.sub(re.escape(START) + r".*?" + re.escape(END), lambda _: block, text, flags=re.S)
        action = "updated"
    else:
        new = (text.rstrip() + "\n\n" if text.strip() else "") + block + "\n"
        action = "added"
    target.write_text(new)
    print(f"bento: {action} pointer block in {target}")


if __name__ == "__main__":
    main()
