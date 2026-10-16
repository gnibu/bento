#!/usr/bin/env python3
"""Reject instruction-file entries that belong somewhere else.

Usage: check_entries.py CURRENT PROPOSED

CURRENT is the instruction file as it is now (AGENTS.md or CLAUDE.md, at any depth; it may
not exist yet), PROPOSED the full text bento-learn wants to write there. Only entries that
are new or changed in PROPOSED are checked, so an old file never blocks a new learning.
An entry (a bullet, a paragraph or a code block) must fit on one line, or on two when it
carries a pointer (a path or a link) to where the detail lives. An AGENTS.md next to a
docs/ directory is also the menu of those docs: each docs/**/*.md must be named in it, by its
path or a folder below docs/ that holds it ("Design briefs → docs/briefs/"). Exits 1 and
names each rejected entry and each doc missing from the menu.
"""
import re
import sys
from pathlib import Path

LINE = 100  # the wrap width of a "line"
BULLET = re.compile(r"\s*([-*+]|\d+\.)\s")
# ponytail: a path-shaped token counts as a pointer, resolved or not; check existence if
# entries start pointing at files that are never written.
POINTER = re.compile(r"\]\(|https?://|\w/[\w.*]|[\w-]\.(md|py|sh|js|ts|tsx|json|toml|ya?ml)\b")


def entries(text):
    """Bullets, paragraphs and code blocks, whitespace-collapsed. Headings and comments are skipped."""
    blocks, current, fenced = [], [], False

    def flush():
        if current:
            blocks.append(" ".join(" ".join(current).split()))
            current.clear()

    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("```"):
            if not fenced:
                flush()
            current.append(stripped)
            fenced = not fenced
            if not fenced:
                flush()
        elif fenced:
            current.append(stripped)
        elif not stripped or stripped.startswith(("#", "<!--")):
            flush()
        else:
            if BULLET.match(line):
                flush()
            current.append(stripped)
    flush()
    return blocks


def problem(entry):
    if len(entry) <= LINE:
        return None
    if len(entry) > 2 * LINE:
        return "over two lines: keep the trigger and a pointer, move the detail to a doc or the code"
    if not POINTER.search(entry):
        return "over one line without a pointer: name the file or link where the detail lives"
    return None


def check(current, proposed):
    old = set(entries(current))
    return [(entry, reason) for entry in entries(proposed)
            if entry not in old and (reason := problem(entry))]


def menu_gaps(root, proposed):
    """Docs under root/docs that the proposed AGENTS.md doesn't name, by file or folder."""
    docs = root / "docs"
    if not docs.is_dir():
        return []
    gaps = []
    for doc in sorted(docs.rglob("*.md")):
        relative = doc.relative_to(root)
        named = [relative.as_posix()] + [f"{folder.as_posix()}/" for folder in relative.parents
                                        if len(folder.parts) > 1]
        if not any(name in proposed for name in named):
            gaps.append(relative.as_posix())
    return gaps


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    current_path = Path(sys.argv[1])
    current = current_path.read_text() if current_path.exists() else ""
    proposed = Path(sys.argv[2]).read_text()
    rejected = check(current, proposed)
    for entry, reason in rejected:
        print(f"{current_path}: {entry[:70]}…: {reason}")
    gaps = menu_gaps(current_path.parent, proposed) if current_path.name == "AGENTS.md" else []
    for doc in gaps:
        print(f"{current_path}: menu misses {doc}: add \"- <when you need it> → {doc}\" under ## Docs")
    sys.exit(1 if rejected or gaps else 0)


if __name__ == "__main__":
    main()
