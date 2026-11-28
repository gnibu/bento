# Rebased branch scope

The recorded reviewed sha `<sha>` is not an ancestor of `HEAD`.

`git rev-list --merges` lists a commit in `origin/<base>..<sha>` or `origin/<base>..HEAD` → the
whole branch (range-diff skips merges).

Otherwise run `git range-diff origin/<base> <sha> HEAD`. Every line up to `<sha>`'s is `=` (same
patch, same order, no `>` commit inserted between them) → its rebased copy (the right-hand sha
on `<sha>`'s line) stands for `<sha>`: record that copy now, then apply the Scope cases in
`SKILL.md` to it. Any `!`, `<` or `>` before it → the whole branch.
