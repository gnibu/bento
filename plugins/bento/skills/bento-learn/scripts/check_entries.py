#!/usr/bin/env python3
"""Reject instruction-file entries that belong somewhere else.

Usage: check_entries.py CURRENT PROPOSED [NEW_DOC...]
       check_entries.py --all FILE...      every entry of each file, as if all were new
       check_entries.py --diff BASE        every AGENTS.md/CLAUDE.md changed since BASE

CURRENT is the instruction file as it is now (AGENTS.md or CLAUDE.md, at any depth; it may
not exist yet), PROPOSED the full text bento-learn wants to write there. Only entries that
are new or changed in PROPOSED are checked, so an old file never blocks a new learning.
`--diff BASE` checks the working tree of each instruction file the branch changed against its
text at the merge base with BASE (a rename: its old path), whoever made the change, and the
docs the branch added beside it as NEW_DOCs; `--all` checks the whole file (a missing one is empty).
An entry (a bullet, a table row, a paragraph or a code block) must fit on one line, or on two when it
carries a pointer (a path or a link) to where the detail lives. An entry outside the bento block
must not restate one of its entries (the file's own block, else the root AGENTS.md's): it loads already.
An AGENTS.md is also the
menu of the docs/**/*.md beside it, tracked or untracked but not ignored, or proposed in the
same change (NEW_DOC, relative to the AGENTS.md's directory): its `## Docs` section must name
each one, by its path or a folder below docs/ that holds it ("Design briefs → docs/briefs/").
An AGENTS.md without a `## Docs` section routes docs its own way: only the NEW_DOCs are checked,
and anywhere in the file. Exits 1 and names each rejected entry and each doc missing from the menu.
It also warns, without failing, about a new root AGENTS.md entry whose paths all sit in one subfolder
(not docs/, and naming no file at the top): it names the nearest AGENTS.md there, or the folder
to create one in. A line changed in place is not new. And it warns when a root AGENTS.md that
grows ends over BUDGET lines outside the bento block (see references/instruction-layer.md).
"""
import difflib
import os
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
BLOCK = re.compile(r"<!-- bento:start -->.*?<!-- bento:end -->", re.S)
BUDGET = 60  # non-blank lines of a root AGENTS.md outside the bento block
# Words too common to tell a restated principle from a repo fact.
STOP = set("""a an the and or but nor to of in on at for by with from into as is are be been was were it its
this that these those there here your you we our they them their not no any every all each when then than so
if else also only just do does did done don't before after while via per run asked ask""".split())


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


def words(text):
    """The entry's content words, lowercased, a plural `s` dropped."""
    found = set()
    for word in re.findall(r"[a-z][a-z0-9-]*", text.lower()):
        word = word.strip("-")
        if len(word) > 3 and word.endswith("s") and not word.endswith("ss"):
            word = word[:-1]
        if word and word not in STOP:
            found.add(word)
    return found


def restates(entry, principles):
    """The bento block entry that entry repeats: at least 3 of its content words, and 70% of
    them, are in that one entry. None if it says something new."""
    own = words(entry)
    for principle in principles:
        shared = len(own & words(principle))
        if shared >= 3 and shared >= 0.7 * len(own):
            return principle
    return None


def outside_block(text):
    return BLOCK.sub("", text)


def block_of(text):
    match = BLOCK.search(text)
    return match.group(0) if match else ""


def over_budget(current, proposed):
    """Lines of proposed outside the bento block, when they pass BUDGET and grew; else None."""
    def size(text):
        return sum(1 for line in outside_block(text).splitlines() if line.strip())
    lines = size(proposed)
    return lines if lines > BUDGET and lines > size(current) else None


def check(current, proposed, loaded=""):
    """(entry, reason) per new entry of proposed that is too long or, outside the bento block,
    repeats one of its entries. The block is proposed's own, else the one `loaded` holds (the
    root AGENTS.md a nested file sits under): only principles the repo actually loads count."""
    principles = entries(block_of(proposed) or block_of(loaded))
    old_block, old_l2 = set(entries(block_of(current))), set(entries(outside_block(current)))
    rejected = [(entry, reason) for entry in entries(block_of(proposed))
                if entry not in old_block and (reason := problem(entry))]
    for entry in entries(outside_block(proposed)):
        if entry in old_l2:
            continue
        reason = problem(entry)
        if not reason and (principle := restates(entry, principles)):
            reason = f"restates the bento block's \"{principle[:60]}…\": drop it"
        if reason:
            rejected.append((entry, reason))
    return rejected


def subfolder(entry, root):
    """The folder below root to hold entry, when its repo paths all sit in one; else None.

    That is the nearest folder with an AGENTS.md over all the paths, else the deepest one
    they share. A file at the top, a dot-folder or docs/ keeps the entry where it is."""
    dirs = []
    text = re.sub(r"https?://\S+|\[[^\]]*\](?=\()", "", entry)  # URLs and link labels
    for token in TOKEN.findall(text):
        token = token.rstrip(".,")
        if "/" not in token:
            if (root / token).is_file():
                return None
            continue
        parts = [part for part in token.split("/") if part not in ("", ".")]
        if token.startswith("/") or ".." in parts or not parts:
            continue
        if parts[0].startswith(".") or parts[0] == "docs":
            return None
        if any("*" in part for part in parts):
            parts = parts[:next(i for i, part in enumerate(parts) if "*" in part)]
        elif not (root / Path(*parts)).is_dir():
            parts = parts[:-1]
        if not parts or not (root / Path(*parts)).is_dir():
            return None
        dirs.append("/".join(parts))
    if not dirs:
        return None
    common = Path(os.path.commonpath(dirs))
    for folder in [common, *common.parents][:-1]:  # never root itself
        if (root / folder / "AGENTS.md").is_file():
            return folder.as_posix()
    return common.as_posix() if common.parts else None


def misplaced(root, current, proposed):
    """New entries whose paths all sit in one subfolder, and that folder. A line changed in
    place (the new line most like a removed one) is not new."""
    old, new = entries(current), entries(proposed)
    added = [entry for entry in new if entry not in old]
    edits = set()
    for gone in (entry for entry in old if entry not in new):
        ratio, edit = max(((difflib.SequenceMatcher(None, entry, gone).ratio(), entry)
                           for entry in added), default=(0, None))
        if ratio > 0.6:
            edits.add(edit)
    return [(entry, folder) for entry in added
            if entry not in edits and (folder := subfolder(entry, root))]


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


def git(cwd, *args):
    return subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True)


def warnings(path, current, proposed):
    """Warning lines for a repository's root AGENTS.md: misplaced entries, then the budget."""
    out = []
    for entry, folder in misplaced(path.parent, current, proposed):
        home = Path(path.parent, folder, "AGENTS.md")
        new = "" if home.exists() else " (new: with a CLAUDE.md holding @AGENTS.md)"
        out.append(f"{path}: warning: {entry[:70]}…: every path is under {folder}/: move it to"
                   f" {folder}/AGENTS.md{new} or {folder}/README.md, unless every task needs it")
    lines = over_budget(current, proposed)
    if lines:
        out.append(f"{path}: warning: {lines} lines outside the bento block, over the {BUDGET}-line"
                   " budget: merge, move or delete stale entries (bento-learn's prune pass)")
    return out


def placement(path):
    """(path is the repository's root AGENTS.md, the root AGENTS.md text a nested file loads with)."""
    top = git(path.parent, "rev-parse", "--show-toplevel").stdout.strip()
    if not top or Path(top).resolve() == path.parent.resolve():
        return path.name == "AGENTS.md", ""
    root = Path(top, "AGENTS.md")
    return False, root.read_text() if root.is_file() else ""


def report(path, current, proposed, new_docs=()):
    """Print what's wrong with proposed as the next text of the instruction file at path.
    True when something fails."""
    at_root, loaded = placement(path)
    rejected = check(current, proposed, loaded)
    gaps = menu_gaps(path.parent, proposed, new_docs) if path.name == "AGENTS.md" else []
    lines = [f"{path}: {entry[:70]}…: {reason}" for entry, reason in rejected]
    lines += [f"{path}: menu misses {doc}: add \"- <when you need it> → {doc}\" under ## Docs,"
              " or where this file routes its docs" for doc in gaps]
    lines += warnings(path, current, proposed) if at_root else []
    for line in lines:
        print(line)
    return bool(rejected or gaps)


def branch_files(top, fork):
    """((old name, name) per file the branch changed or left untracked, names it added)."""
    fields = git(top, "diff", "--name-status", "-z", "-M", "--diff-filter=d", fork).stdout.split("\0")
    moves, added = [], []
    while len(fields) > 1:
        size = 3 if fields[0][:1] in "RC" else 2  # a rename or copy names its source too
        status, *names = fields[:size]
        fields = fields[size:]
        moves.append((names[0], names[-1]))
        if status == "A":
            added.append(names[-1])
    untracked = [name for name in git(top, "ls-files", "-z", "--others", "--exclude-standard")
                 .stdout.split("\0") if name]
    return moves + [(name, name) for name in untracked], added + untracked


def instruction_file(top, path):
    """True for an AGENTS.md/CLAUDE.md that is, or links to, a file inside the checkout."""
    return path.name in ("AGENTS.md", "CLAUDE.md") and path.is_file() and top in path.resolve().parents


def docs_beside(name, added):
    """The added docs/**/*.md under the instruction file `name`'s folder, relative to it."""
    docs = Path(name).parent / "docs"
    return [Path(doc).relative_to(docs.parent).as_posix() for doc in added
            if doc.endswith(".md") and docs in Path(doc).parents]


def changed(base):
    """(path, text at the merge base, docs the branch added beside it) per AGENTS.md/CLAUDE.md
    the branch changed, worktree included. A renamed file keeps its old text; a symlink is its
    target, once, and only inside the repository."""
    top = Path(git(".", "rev-parse", "--show-toplevel").stdout.strip()).resolve()
    fork = git(top, "merge-base", base, "HEAD")
    if fork.returncode:
        sys.exit(f"check_entries: no merge base with {base}: {fork.stderr.strip()}")
    fork = fork.stdout.strip()
    moves, added = branch_files(top, fork)
    seen, out = set(), []
    for old_name, name in moves:
        path = top / name
        if not instruction_file(top, path) or path.resolve() in seen:
            continue
        seen.add(path.resolve())
        if path.resolve() != path:  # a CLAUDE.md symlink: its target's old text
            old_name = path.resolve().relative_to(top).as_posix()
        old = git(top, "show", f"{fork}:{old_name}")
        out.append((path, old.stdout if old.returncode == 0 else "", docs_beside(name, added)))
    return out


def main():
    args = sys.argv[1:]
    read = lambda name: Path(name).read_text() if Path(name).exists() else ""
    if args[:1] == ["--diff"] and len(args) == 2:
        failed = [report(path, old, path.read_text(), docs) for path, old, docs in changed(args[1])]
    elif args[:1] == ["--all"] and len(args) > 1:
        failed = [report(Path(name), "", read(name)) for name in args[1:]]
    elif len(args) >= 2 and not args[0].startswith("--"):
        failed = [report(Path(args[0]), read(args[0]), Path(args[1]).read_text(), args[2:])]
    else:
        sys.exit(__doc__)
    sys.exit(1 if any(failed) else 0)


if __name__ == "__main__":
    main()
