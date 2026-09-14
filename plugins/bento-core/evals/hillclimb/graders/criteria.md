---
type: llm
weight: 1
---

Score how well the response applies **hillclimb** discipline. A strong answer covers most
of:

- **Freeze the measurement harness first** — fix the dataset/metric/how-measured before
  tuning, and record a baseline number.
- **One variable at a time** — change a single knob per experiment; never stack untested
  changes.
- **Keep-or-revert, logged** — accept only a real (non-noise) gain, and log every attempt
  and its outcome.
- **Don't stop on a lucky first hit** — enough iterations / a stated stop condition.

Full credit: freeze-baseline + one-variable + keep-or-revert-log all present. Partial: only
"be systematic / measure things" without the one-variable rule or a decision log. Low: no
notion of isolating variables against a fixed baseline.
