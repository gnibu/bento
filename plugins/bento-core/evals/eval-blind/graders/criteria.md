---
type: llm
weight: 1
---

Score how well the response applies **blind evaluation** discipline. A strong answer covers
most of:

- **Neutralize labels** — rename the two variants to neutral names (A/B) and hide which is
  the new/preferred one from whoever/whatever judges.
- **Blind judge** — the scorer (a separate pass or person) does not know which output is
  which while scoring.
- **Grade behavior, not claims** — judge the actual outputs/transcripts, not a model's
  self-report that it did well.
- **Same fixed input set** for both variants; unblind only after scores are locked.

Full credit: neutral labels + blind judge + grade-behavior all present. Partial: only
generic "test both / define metrics" advice without the blinding mechanism. Low: no notion
of removing bias from the judge.
