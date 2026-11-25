#!/usr/bin/env python3
"""Reject instruction-file entries that belong somewhere else.

Usage: check_entries.py CURRENT PROPOSED [NEW_DOC...]

CURRENT is the instruction file as it is now (AGENTS.md or CLAUDE.md, at any depth; it may
not exist yet), PROPOSED the full text bento-learn wants to write there. Only entries that
are new or changed in PROPOSED are checked, so an old file never blocks a new learning.
An entry (a bullet, a table row, a paragraph or a code block) must fit on one line, or on two when it
carries a pointer (a path or a link) to where the detail lives. An AGENTS.md is also the
menu of the docs/**/*.md beside it, tracked or untracked but not ignored, or proposed in the
same change (NEW_DOC, relative to the AGENTS.md's directory): its `## Docs` section must name
each one, by its path or a folder below docs/ that holds it ("Design briefs → docs/briefs/").
An AGENTS.md without a `## Docs` section routes docs its own way: only the NEW_DOCs are checked,
and anywhere in the file. Exits 1 and names each rejected entry and each doc missing from the menu.
It also warns, without failing, about a new entry whose repo paths all sit under one subfolder
(not docs/, and naming no file at the top): it names the nearest AGENTS.md there, or the folder
to create one in. A line changed in place is not new.
"""
import difflib
import re
import subprocess
import sys
from pathlib import Path

LINE = 100  # the wrap width of a "line"
BULLET = re.compile(r"\s*([-*+]|\d+\.)\s")
# ponytail: a path-shaped token counts as a pointer, resolved or not; check existence if
# entries start pointing at files that are never written.
POINTER = re.compile(r"\]\(|https?://|\w/[\w.*]|[\w-]\.(md|py|sh|js|ts|tsx|json|toml|ya?ml)\b")
# A path-like token, not inside a home (~/), variable ($X/) or absolute path.
TOKEN = re.compile(r"(?<![\w~$/.-])[\w.*/-]+")


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
            if BULLET.match(line) or stripped.startswith("|"):  # a table row is its own entry
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


def subfolder(entry, root):
    """The folder below root to hold entry, when its repo paths all sit in one; else None.

    That is the nearest folder with an AGENTS.md over all the paths, else the deepest one
    they share. A file at the top, a dot-folder or docs/ keeps the entry where it is."""
    dirs = []
    for token in TOKEN.findall(re.sub(r"https?://\S+", "", entry)):
        token = token.rstrip(".,")
        parts = [part for part in token.split("/") if part not in ("", ".")]
        if "/" not in token:
            if "." in token and (root / token).is_file():
                return None
            continue
        if token.startswith("/") or not parts or parts[0] == "..":
            continue
        if parts[0].startswith(".") or parts[0] == "docs":
            return None
        if not (root / Path(*parts)).is_dir():
            parts = parts[:-1]
        if not parts or not (root / Path(*parts)).is_dir():
            return None
        dirs.append(parts)
    if not dirs:
        return None
    common = []
    for level in zip(*dirs):
        if len(set(level)) > 1:
            break
        common.append(level[0])
    for depth in range(len(common), 0, -1):
        if (root / Path(*common[:depth]) / "AGENTS.md").is_file():
            return "/".join(common[:depth])
    return "/".join(common) or None


def misplaced(root, current, proposed):
    """New entries whose paths all sit in one subfolder, and that folder. A line changed in
    place (close to one removed line, each removed line used once) is not new."""
    old, new = entries(current), entries(proposed)
    removed = [entry for entry in old if entry not in new]
    found = []
    for entry in new:
        if entry in old:
            continue
        edit = next((gone for gone in removed
                     if difflib.SequenceMatcher(None, entry, gone).ratio() > 0.6), None)
        if edit is not None:
            removed.remove(edit)
        elif folder := subfolder(entry, root):
            found.append((entry, folder))
    return found


def menu_section(text):
    """The body of the `## Docs` section, up to the next heading of level 1 or 2; None without one."""
    match = re.search(r"^## Docs[ \t]*\n(.*?)(?=^#{1,2} |\Z)", text, re.M | re.S)
    return match.group(1) if match else None


def disk_docs(root):
    """docs/**/*.md under root that git doesn't ignore; every one outside a git repository."""
    # -z: without it git quotes non-ASCII names (docs/résumé.md) and is_file() drops them.
    listed = subprocess.run(["git", "-C", str(root), "ls-files", "-z", "--cached", "--others",
                             "--exclude-standard", "--", "docs/*.md"], capture_output=True, text=True)
    if listed.returncode:
        return {doc.relative_to(root).as_posix() for doc in (root / "docs").rglob("*.md")}
    return {doc for doc in listed.stdout.split("\0") if doc and (root / doc).is_file()}


def menu_gaps(root, proposed, new_docs=()):
    """Docs under root/docs, plus new_docs, that the proposed `## Docs` menu doesn't name.

    Without a `## Docs` section, only new_docs count, named anywhere in proposed."""
    docs = {Path(doc).as_posix() for doc in new_docs}
    menu = menu_section(proposed)
    if menu is None:
        menu = proposed
    else:
        docs |= disk_docs(root)
    gaps = []
    for doc in sorted(docs):
        folders = [f"{folder.as_posix()}/" for folder in Path(doc).parents if len(folder.parts) > 1]
        # A name counts only as a whole target: `docs/a/b.md` doesn't name the folder `docs/a/`.
        if not any(re.search(re.escape(name) + r"(?![\w/-]|\.\w)", menu) for name in [doc, *folders]):
            gaps.append(doc)
    return gaps


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    current_path = Path(sys.argv[1])
    current = current_path.read_text() if current_path.exists() else ""
    proposed = Path(sys.argv[2]).read_text()
    rejected = check(current, proposed)
    for entry, reason in rejected:
        print(f"{current_path}: {entry[:70]}…: {reason}")
    gaps = (menu_gaps(current_path.parent, proposed, sys.argv[3:])
            if current_path.name == "AGENTS.md" else [])
    for doc in gaps:
        print(f"{current_path}: menu misses {doc}: add \"- <when you need it> → {doc}\" under ## Docs,"
              " or where this file routes its docs")
    for entry, folder in misplaced(current_path.parent, current, proposed):
        home = Path(current_path.parent, folder, "AGENTS.md")
        new = "" if home.exists() else " (new: with a CLAUDE.md holding @AGENTS.md)"
        print(f"{current_path}: warning: {entry[:70]}…: every path is under {folder}/: propose"
              f" {folder}/AGENTS.md{new} or {folder}/README.md instead")
    sys.exit(1 if rejected or gaps else 0)


if __name__ == "__main__":
    main()
